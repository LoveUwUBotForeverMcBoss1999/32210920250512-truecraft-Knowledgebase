from flask import Flask, render_template, abort, request, jsonify
import os
import markdown
import frontmatter
from pathlib import Path
import re

app = Flask(__name__)


def load_page(page_name):
    """Load a markdown page with frontmatter"""
    page_path = Path(f'pages/{page_name}.md')
    if not page_path.exists():
        return None

    try:
        with open(page_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        # Convert markdown to HTML
        html_content = markdown.markdown(post.content, extensions=['fenced_code', 'tables', 'toc'])

        return {
            'title': post.metadata.get('title', page_name),
            'description': post.metadata.get('description', ''),
            'category': post.metadata.get('category', 'General'),
            'content': html_content,
            'slug': page_name
        }
    except Exception as e:
        print(f"Error loading page {page_name}: {e}")
        return None


def get_all_pages():
    """Get all available pages with their metadata"""
    pages_dir = Path('pages')
    if not pages_dir.exists():
        return []

    pages = []
    for md_file in pages_dir.glob('*.md'):
        page_name = md_file.stem
        page_data = load_page(page_name)
        if page_data:
            pages.append(page_data)

    return pages


def get_categories():
    """Get all unique categories from pages"""
    pages = get_all_pages()
    categories = {}

    for page in pages:
        category = page['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(page)

    return categories


@app.route('/')
def index():
    """Homepage with categorized pages"""
    categories = get_categories()
    # Calculate total pages count
    total_pages = sum(len(pages) for pages in categories.values())
    return render_template('index.html', categories=categories, total_pages=total_pages)


@app.route('/page/<page_name>')
def page(page_name):
    """Individual page view"""
    page_data = load_page(page_name)
    if not page_data:
        abort(404)

    return render_template('page.html', page=page_data)


@app.route('/search')
def search():
    """Search endpoint"""
    query = request.args.get('q', '').lower().strip()
    if not query:
        return jsonify([])

    pages = get_all_pages()
    results = []

    for page in pages:
        # Search in title, description, and content
        searchable_text = f"{page['title']} {page['description']} {page['content']}".lower()
        if query in searchable_text:
            results.append({
                'title': page['title'],
                'description': page['description'],
                'category': page['category'],
                'url': f'/page/{page["slug"]}'
            })

    return jsonify(results)


@app.route('/category/<category_name>')
def category(category_name):
    """Category page"""
    categories = get_categories()
    if category_name not in categories:
        abort(404)

    pages = categories[category_name]
    return render_template('category.html', category=category_name, pages=pages)


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
