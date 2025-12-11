"""
Visualization functions for Synapse Wrapped metrics.
"""

import base64
import io
from collections import Counter
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
from wordcloud import WordCloud


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def create_files_downloaded_card(file_count: int, total_size: int) -> str:
    """Create HTML card for files downloaded metric."""
    size_str = format_bytes(total_size)
    return f"""
    <div class="wrapped-card">
        <h2 class="card-title">Files Downloaded</h2>
        <div class="metric-large">{file_count:,}</div>
        <div class="metric-subtitle">Total Size: {size_str}</div>
    </div>
    """


def create_top_projects_card(top_projects_df: pd.DataFrame) -> str:
    """Create HTML card for top 5 projects."""
    if top_projects_df.empty:
        return """
        <div class="wrapped-card">
            <h2 class="card-title">Top Projects</h2>
            <div class="metric-subtitle">No project data available</div>
        </div>
        """
    
    html = '<div class="wrapped-card"><h2 class="card-title">Top 5 Projects</h2><div class="project-list">'
    for idx, row in top_projects_df.iterrows():
        project_name = row.get('project_name', f"Project {row.get('project_id', 'Unknown')}")
        file_count = row.get('file_count', 0)
        html += f"""
        <div class="project-item">
            <div class="project-rank">{idx + 1}</div>
            <div class="project-info">
                <div class="project-name">{project_name}</div>
                <div class="project-metric">{file_count:,} files</div>
            </div>
        </div>
        """
    html += '</div></div>'
    return html


def create_wordcloud_image(project_names: List[str], dark_mode: bool = False) -> str:
    """Create word cloud image and return as base64 encoded string."""
    if not project_names:
        return ""
    
    # Remove duplicates, None values, and 'None' strings
    unique_names = list(set([
        str(name).strip() for name in project_names 
        if name and str(name).strip() and str(name).strip().lower() != 'none'
    ]))
    
    # Split project names into words and create a frequency dictionary
    word_freq = Counter()
    
    # Common stop words to filter out
    stop_words = {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'are', 'was', 'were', 
                  'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might',
                  'project', 'study', 'data', 'analysis', 'research', 'of', 'a', 'an', 'in', 'on', 'at', 'to',
                  'using', 'based', 'new', 'via', 'none', 'null', 'nan'}
    
    for name in unique_names:
        # Split on common delimiters and add individual words
        words = str(name).replace('_', ' ').replace('-', ' ').replace('.', ' ').split()
        for word in words:
            word_lower = word.lower().strip()
            # Filter out very short words, numbers, and common stop words
            if (len(word_lower) > 2 and 
                word_lower not in stop_words and 
                not word_lower.isdigit() and
                word_lower.isalpha()):
                word_freq[word_lower] += 1
    
    # Generate word cloud from frequency dictionary
    if not word_freq:
        return ""
    
    # Use dark mode compatible colors
    bg_color = '#0a0a0f' if dark_mode else 'white'
    color_func = None
    if dark_mode:
        # Neon cyan/magenta color palette for dark mode
        def neon_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
            import random
            colors = ['#00fff7', '#ff00ff', '#00ffaa', '#ff6b6b', '#4ecdc4', '#a855f7', '#22d3ee']
            return random.choice(colors)
        color_func = neon_color_func
    
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color=bg_color,
        colormap=None if dark_mode else 'viridis',
        color_func=color_func,
        max_words=80,
        relative_scaling=0.5,
        prefer_horizontal=0.7,
        collocations=False  # Prevents repeated word combinations
    ).generate_from_frequencies(word_freq)
    
    # Convert to base64
    img_buffer = io.BytesIO()
    fig = plt.figure(figsize=(10, 5))
    if dark_mode:
        fig.patch.set_facecolor('#0a0a0f')
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150, 
                facecolor='#0a0a0f' if dark_mode else 'white')
    plt.close()
    
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.read()).decode()
    return img_base64


def create_projects_wordcloud_card(project_count: int, project_names: List[str], dark_mode: bool = True) -> str:
    """Create HTML card for projects accessed with word cloud."""
    img_base64 = create_wordcloud_image(project_names, dark_mode=dark_mode)
    img_tag = f'<img src="data:image/png;base64,{img_base64}" class="wordcloud-img" alt="Project word cloud" />' if img_base64 else ""
    
    return f"""
    <div class="wrapped-card">
        <h2 class="card-title">Projects Explored</h2>
        <div class="metric-large">{project_count}</div>
        <div class="metric-subtitle">unique projects accessed</div>
        {img_tag}
    </div>
    """


def create_active_days_card(active_days: int, year: int) -> str:
    """Create HTML card for active days."""
    return f"""
    <div class="wrapped-card">
        <h2 class="card-title">Days Active</h2>
        <div class="metric-large">{active_days}</div>
        <div class="metric-subtitle">days on Synapse in {year}</div>
    </div>
    """


def create_creations_card(creations_df: pd.DataFrame) -> str:
    """Create HTML card for projects, files, tables created."""
    if creations_df.empty:
        return """
        <div class="wrapped-card">
            <h2 class="card-title">Content Created</h2>
            <div class="metric-subtitle">No creations this year</div>
        </div>
        """
    
    # Handle different possible column names (case-insensitive)
    count_col = None
    for col in creations_df.columns:
        if 'count' in col.lower() or 'creation' in col.lower():
            count_col = col
            break
    
    if count_col is None:
        # Try to find any numeric column
        numeric_cols = creations_df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            count_col = numeric_cols[0]
        else:
            return """
            <div class="wrapped-card">
                <h2 class="card-title">Content Created</h2>
                <div class="metric-subtitle">Unable to parse creation data</div>
            </div>
            """
    
    total_creations = int(creations_df[count_col].sum())
    
    # Find node_type column
    type_col = None
    for col in creations_df.columns:
        if 'type' in col.lower() or 'node' in col.lower():
            type_col = col
            break
    
    if type_col:
        projects = int(creations_df[creations_df[type_col] == 'project'][count_col].sum()) if len(creations_df[creations_df[type_col] == 'project']) > 0 else 0
        files = int(creations_df[creations_df[type_col] == 'file'][count_col].sum()) if len(creations_df[creations_df[type_col] == 'file']) > 0 else 0
        tables = int(creations_df[creations_df[type_col] == 'table'][count_col].sum()) if len(creations_df[creations_df[type_col] == 'table']) > 0 else 0
    else:
        # If we can't find node_type, just show total
        projects = files = tables = 0
    
    return f"""
    <div class="wrapped-card">
        <h2 class="card-title">Content Created</h2>
        <div class="metric-large">{total_creations:,}</div>
        <div class="creation-breakdown">
            <div class="creation-item">{projects} projects</div>
            <div class="creation-item">{files} files</div>
            <div class="creation-item">{tables} tables</div>
        </div>
    </div>
    """


def create_network_graph(collaboration_df: pd.DataFrame, user_id: int, user_name: str, dark_mode: bool = True) -> str:
    """Create network visualization and return as base64 encoded image."""
    if collaboration_df.empty:
        return ""
    
    # Find the user_id column (case-insensitive)
    user_id_col = None
    for col in collaboration_df.columns:
        if col.lower() == 'user_id':
            user_id_col = col
            break
    
    if user_id_col is None:
        # If no user_id column, can't create network
        return ""
    
    # Create network graph
    G = nx.Graph()
    
    # Color scheme for dark mode
    if dark_mode:
        central_color = '#00fff7'  # Neon cyan
        collab_color = '#a855f7'   # Purple
        edge_color = '#00fff7'
        label_color = '#ffffff'
        bg_color = '#0a0a0f'
    else:
        central_color = '#125E81'
        collab_color = '#E9B4CE'
        edge_color = '#636E83'
        label_color = '#333333'
        bg_color = 'white'
    
    # Add central user node
    G.add_node(user_id, label=user_name, size=50, color=central_color)
    
    # Add collaborator nodes and edges
    top_collaborators = collaboration_df.head(20)  # Limit to top 20 for visualization
    for _, row in top_collaborators.iterrows():
        collab_id = row[user_id_col]
        collab_name = row.get('collaborator_name', f"User {collab_id}")
        # Use shared_files as the weight (number of overlapping files downloaded)
        shared_files = row.get('shared_files', row.get('collaboration_score', 0))
        
        # Node size based on number of overlapping files
        node_size = min(30 + int(shared_files / 100), 50)  # Scale based on file count
        G.add_node(collab_id, label=collab_name, size=node_size, color=collab_color)
        # Edge weight is the number of overlapping files
        G.add_edge(user_id, collab_id, weight=int(shared_files))
    
    # Create matplotlib figure
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Draw nodes
    node_colors = [G.nodes[node].get('color', collab_color) for node in G.nodes()]
    node_sizes = [G.nodes[node].get('size', 20) * 10 for node in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, alpha=0.9, ax=ax)
    # Draw edges with width based on weight (overlapping files)
    edge_widths = [G[u][v].get('weight', 1) / 1000 for u, v in G.edges()]  # Scale for visibility
    edge_widths = [max(0.5, min(w, 3)) for w in edge_widths]  # Clamp between 0.5 and 3
    nx.draw_networkx_edges(G, pos, alpha=0.5 if dark_mode else 0.4, width=edge_widths, 
                          edge_color=edge_color, ax=ax)
    
    # Draw labels only for central user and top collaborators
    labels = {node: G.nodes[node].get('label', str(node)) for node in G.nodes()}
    # Only show labels for central user and top 5 collaborators
    if user_id_col:
        top_5_ids = set(collaboration_df.head(5)[user_id_col].tolist() + [user_id])
    else:
        top_5_ids = {user_id}
    labels_to_show = {node: label for node, label in labels.items() if node in top_5_ids}
    nx.draw_networkx_labels(G, pos, labels_to_show, font_size=9, font_weight='bold', 
                           font_color=label_color, ax=ax)
    
    ax.axis('off')
    plt.tight_layout()
    
    # Convert to base64
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150, facecolor=bg_color)
    plt.close()
    
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.read()).decode()
    return img_base64


def create_network_card(collaboration_df: pd.DataFrame, user_id: int, user_name: str, dark_mode: bool = True) -> str:
    """Create HTML card for collaboration network."""
    if collaboration_df.empty:
        return """
        <div class="wrapped-card">
            <h2 class="card-title">Collaboration Network</h2>
            <div class="metric-subtitle">No collaboration data available</div>
        </div>
        """
    
    img_base64 = create_network_graph(collaboration_df, user_id, user_name, dark_mode=dark_mode)
    img_tag = f'<img src="data:image/png;base64,{img_base64}" class="network-img" alt="Collaboration network" />' if img_base64 else ""
    
    return f"""
    <div class="wrapped-card">
        <h2 class="card-title">Your Collaboration Network</h2>
        <div class="metric-subtitle">Users who downloaded the same files as you</div>
        {img_tag}
    </div>
    """


def create_top_collaborators_card(collaborators_df: pd.DataFrame) -> str:
    """Create HTML card for top 5 collaborators."""
    if collaborators_df.empty:
        return """
        <div class="wrapped-card">
            <h2 class="card-title">Top Collaborators</h2>
            <div class="metric-subtitle">No collaborator data available</div>
        </div>
        """
    
    html = '<div class="wrapped-card"><h2 class="card-title">Top 5 Collaborators</h2><div class="collaborator-list">'
    for idx, row in collaborators_df.iterrows():
        collab_name = row.get('collaborator_name', f"User {row.get('user_id', 'Unknown')}")
        score = row.get('collaboration_score', 0)
        shared_projects = row.get('shared_projects', 0)
        shared_files = row.get('shared_files', 0)
        
        html += f"""
        <div class="collaborator-item">
            <div class="collaborator-rank">{idx + 1}</div>
            <div class="collaborator-info">
                <div class="collaborator-name">{collab_name}</div>
                <div class="collaborator-metric">{shared_projects} projects, {shared_files} files</div>
            </div>
        </div>
        """
    html += '</div></div>'
    return html

