import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from help import (
    find_repo_root,
    get_current_branch,
    read_git_object,
    get_all_commits
)


def get_all_branches():
    """Get all branches and their commit IDs."""
    repo_root = find_repo_root()
    branches_dir = os.path.join(repo_root, ".mygit", "refs", "heads")
    
    branches = {}
    if os.path.exists(branches_dir):
        for branch_name in os.listdir(branches_dir):
            branch_path = os.path.join(branches_dir, branch_name)
            with open(branch_path, "r") as f:
                commit_id = f.read().strip()
                branches[branch_name] = commit_id
    
    return branches


def build_commit_graph():
    """Build a graph structure of commits with their parents."""
    commits = {}
    all_commit_ids = get_all_commits()
    
    for commit_id in all_commit_ids:
        try:
            raw_content = read_git_object(commit_id)
            content = raw_content.decode("utf-8")
            
            lines = content.split("\n")
            parents = []
            message = ""
            
            in_message = False
            for line in lines:
                if line.startswith("parent "):
                    parents.append(line.split(" ", 1)[1])
                elif line == "" and not in_message:
                    in_message = True
                elif in_message and line.strip():
                    message = line.strip()
                    break
            
            commits[commit_id] = {
                "parents": parents,
                "message": message
            }
        except Exception:
            continue
    
    return commits


def generate_commit_graph_image(output_file="commit_graph.png"):
    """
    Generate a graphical image of the commit tree.
    
    Args:
        output_file: Path to save the image file
    """
    # Get data
    current_branch = get_current_branch()
    branches = get_all_branches()
    commits = build_commit_graph()
    all_commit_ids = get_all_commits()
    
    if not commits:
        print("No commits found.")
        return
    
    # Map commits to branches
    commit_to_branches = {}
    for branch_name, commit_id in branches.items():
        if commit_id not in commit_to_branches:
            commit_to_branches[commit_id] = []
        commit_to_branches[commit_id].append(branch_name)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, max(8, len(all_commit_ids) * 1.5)))
    ax.set_xlim(-1, 10)
    ax.set_ylim(-len(all_commit_ids) - 1, 1)
    ax.axis('off')
    
    # Title
    fig.suptitle('Commit Graph', fontsize=20, fontweight='bold', y=0.98)
    
    # Draw commits from top to bottom
    y_position = 0
    commit_positions = {}
    
    for i, commit_id in enumerate(all_commit_ids):
        commit_data = commits.get(commit_id, {})
        short_hash = commit_id[:10]
        message = commit_data.get("message", "")
        
        # Store position
        commit_positions[commit_id] = (3, y_position)
        
        # Determine color based on position
        if i == 0:
            node_color = '#4CAF50'  # Green for latest
        else:
            node_color = '#FFC107'  # Amber for others
        
        # Draw commit node (circle)
        circle = plt.Circle((3, y_position), 0.3, color=node_color, ec='black', linewidth=2, zorder=3)
        ax.add_patch(circle)
        
        # Draw commit hash
        ax.text(3.7, y_position, short_hash, fontsize=11, fontweight='bold', 
                va='center', fontfamily='monospace')
        
        # Draw commit message
        if message:
            wrapped_message = message[:40] + "..." if len(message) > 40 else message
            ax.text(3.7, y_position - 0.25, wrapped_message, fontsize=9, 
                    va='top', style='italic', color='#555')
        
        # Draw branch labels
        if commit_id in commit_to_branches:
            x_offset = 6.5
            for branch_name in commit_to_branches[commit_id]:
                if branch_name == current_branch:
                    # Current branch with HEAD
                    # Draw HEAD label
                    head_box = FancyBboxPatch((x_offset - 0.1, y_position - 0.2), 
                                             0.8, 0.4,
                                             boxstyle="round,pad=0.05",
                                             facecolor='#00BCD4', 
                                             edgecolor='black',
                                             linewidth=1.5,
                                             zorder=2)
                    ax.add_patch(head_box)
                    ax.text(x_offset + 0.3, y_position, 'HEAD', fontsize=9, 
                           fontweight='bold', va='center', ha='center', color='white')
                    
                    x_offset += 1.2
                    
                    # Draw arrow
                    ax.annotate('', xy=(x_offset + 0.3, y_position), 
                               xytext=(x_offset, y_position),
                               arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
                    
                    x_offset += 0.3
                    
                    # Draw branch label
                    branch_box = FancyBboxPatch((x_offset - 0.1, y_position - 0.2), 
                                               len(branch_name) * 0.12 + 0.3, 0.4,
                                               boxstyle="round,pad=0.05",
                                               facecolor='#2196F3',
                                               edgecolor='black',
                                               linewidth=1.5,
                                               zorder=2)
                    ax.add_patch(branch_box)
                    ax.text(x_offset + len(branch_name) * 0.06 + 0.05, y_position, 
                           branch_name, fontsize=9, fontweight='bold', 
                           va='center', ha='center', color='white')
                    x_offset += len(branch_name) * 0.12 + 0.5
                else:
                    # Other branches
                    branch_box = FancyBboxPatch((x_offset - 0.1, y_position - 0.2), 
                                               len(branch_name) * 0.12 + 0.3, 0.4,
                                               boxstyle="round,pad=0.05",
                                               facecolor='#9C27B0',
                                               edgecolor='black',
                                               linewidth=1.5,
                                               zorder=2)
                    ax.add_patch(branch_box)
                    ax.text(x_offset + len(branch_name) * 0.06 + 0.05, y_position, 
                           branch_name, fontsize=9, fontweight='bold', 
                           va='center', ha='center', color='white')
                    x_offset += len(branch_name) * 0.12 + 0.5
        
        y_position -= 1.5
    
    # Draw parent connections
    for commit_id in all_commit_ids:
        commit_data = commits.get(commit_id, {})
        parents = commit_data.get("parents", [])
        
        if commit_id in commit_positions:
            x1, y1 = commit_positions[commit_id]
            
            for parent_id in parents:
                if parent_id in commit_positions:
                    x2, y2 = commit_positions[parent_id]
                    
                    # Draw arrow from child to parent
                    arrow = FancyArrowPatch((x1, y1 - 0.3), (x2, y2 + 0.3),
                                          arrowstyle='->', 
                                          color='#2196F3',
                                          linewidth=2,
                                          mutation_scale=20,
                                          zorder=1)
                    ax.add_patch(arrow)
    
    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor='#4CAF50', edgecolor='black', label='Latest Commit'),
        mpatches.Patch(facecolor='#FFC107', edgecolor='black', label='Older Commits'),
        mpatches.Patch(facecolor='#00BCD4', edgecolor='black', label='HEAD Pointer'),
        mpatches.Patch(facecolor='#2196F3', edgecolor='black', label='Current Branch'),
        mpatches.Patch(facecolor='#9C27B0', edgecolor='black', label='Other Branches'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"Commit graph saved to: {output_file}")
    
    return output_file


if __name__ == "__main__":
    generate_commit_graph_image()
