import os
from flask import Flask, render_template, abort, request, jsonify
from pathlib import Path
import markdown
import frontmatter

# Base directory for the project
BASE_DIR = Path(__file__).parent.resolve()

# Initialize Flask app
app = Flask(
    __name__,
    template_folder=BASE_DIR / "templates",
    static_folder=BASE_DIR / "static"
)

def load_page(page_name):
    """Load a markdown page and convert to HTML"""
    page_path = BASE_DIR / "pages" / f"{page_name}.md"
    if not page_path.exists():
        return None
    try:
        with open(page_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)
        html_content = markdown.markdown(
            post.content,
            extensions=['fenced_code', 'tables', 'toc']
        )
        return {
            "title": post.metadata.get("title", page_name),
            "description": post.metadata.get("description", ""),
            "category": post.metadata.get("category", "General"),
            "content": html_content,
            "slug": page_name
        }
    except Exception as e:
        print(f"Error loading page {page_name}: {e}")
        return None

def get_all_pages():
    """Return all markdown pages with metadata"""
    pages_dir = BASE_DIR / "pages"
    if not pages_dir.exists():
        return []
    pages = []
    for md_file in pages_dir.glob("*.md"):
        page_data = load_page(md_file.stem)
        if page_data:
            pages.append(page_data)
    return pages

def get_categories():
    """Return a dictionary of categories mapping to pages"""
    pages = get_all_pages()
    categories = {}
    for page in pages:
        category = page["category"]
        categories.setdefault(category, []).append(page)
    return categories

@app.route("/")
def index():
    """Homepage showing pages categorized"""
    categories = get_categories()
    total_pages = sum(len(pages) for pages in categories.values())
    return render_template("index.html", categories=categories, total_pages=total_pages)

@app.route("/page/<page_name>")
def page(page_name):
    """Render individual page"""
    page_data = load_page(page_name)
    if not page_data:
        abort(404)
    return render_template("page.html", page=page_data)

@app.route("/search")
def search():
    """Search endpoint returning JSON results"""
    query = request.args.get("q", "").lower().strip()
    if not query:
        return jsonify([])
    results = []
    for page in get_all_pages():
        searchable_text = f"{page['title']} {page['description']} {page['content']}".lower()
        if query in searchable_text:
            results.append({
                "title": page["title"],
                "description": page["description"],
                "category": page["category"],
                "url": f"/page/{page['slug']}"
            })
    return jsonify(results)

@app.route("/category/<category_name>")
def category(category_name):
    """Render pages for a specific category"""
    categories = get_categories()
    if category_name not in categories:
        abort(404)
    return render_template("category.html", category=category_name, pages=categories[category_name])

@app.errorhandler(404)
def not_found(error):
    """Custom 404 page"""
    return render_template("404.html"), 404

# Add this at the end for Vercel
if __name__ == "__main__":
    app.run(debug=True)

# This is crucial for Vercel to recognize the app
app = app

