import os
import sys
import time
import hashlib
import zlib
import glob
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
except ImportError:
    print("Error: matplotlib is required. Please install it with 'pip install matplotlib'.")
    sys.exit(1)

# Helper to read git objects directly if modules fail
def read_git_object_fallback(object_hash):
    path = os.path.join(".mygit", "objects", object_hash[:2], object_hash[2:])
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = zlib.decompress(f.read())
    # Skip header
    null_idx = data.find(b'\0')
    return data[null_idx+1:]

try:
    from blob import read_git_object
    from help import find_repo_root
except ImportError:
    # Fallback if running standalone without simplified path
    read_git_object = read_git_object_fallback
    find_repo_root = lambda: os.getcwd()

class CommitGraph:
    def __init__(self):
        self.commits = {}  # id -> metadata
        self.branches = {} # name -> commit_id
        self.head_commit = None
        self.root_commits = []
    
    def load(self):
        # 1. Find Repo Root
        try:
            repo_root = find_repo_root()
            os.chdir(repo_root)
        except Exception as e:
            print(f"Error finding repo root: {e}")
            sys.exit(1)

        if not os.path.isdir(".mygit"):
            print("Error: .mygit directory not found.")
            sys.exit(1)

        # 2. Read Branches
        refs_dir = os.path.join(".mygit", "refs", "heads")
        if os.path.exists(refs_dir):
            for branch_name in os.listdir(refs_dir):
                path = os.path.join(refs_dir, branch_name)
                with open(path, "r") as f:
                    commit_id = f.read().strip()
                    self.branches[branch_name] = commit_id

        # 3. Read HEAD
        head_path = os.path.join(".mygit", "HEAD")
        if os.path.exists(head_path):
            with open(head_path, "r") as f:
                content = f.read().strip()
                if content.startswith("ref:"):
                    # HEAD points to branch
                    ref = content.split(" ")[1]
                    branch_name = os.path.basename(ref)
                    if branch_name in self.branches:
                        self.head_commit = self.branches[branch_name]
                else:
                    # Detached HEAD
                    self.head_commit = content

        # 4. Traverse History (Graph Discovery)
        # Start from all branch tips + HEAD
        start_nodes = list(self.branches.values())
        if self.head_commit:
            start_nodes.append(self.head_commit)
        
        queue = list(set(start_nodes)) # Unique
        visited = set()

        while queue:
            commit_id = queue.pop(0)
            if commit_id in visited or not commit_id:
                continue
            visited.add(commit_id)

            # Parse commit
            try:
                data = read_git_object(commit_id)
                if not data:
                    continue
                text = data.decode('utf-8', errors='replace')
                
                parents = []
                lines = text.split('\n')
                for line in lines:
                    if line.startswith('parent '):
                        parents.append(line.split(' ')[1])
                    elif line == '':
                        break
                
                # Store
                if commit_id not in self.commits:
                    self.commits[commit_id] = {
                        'id': commit_id,
                        'parents': parents,
                        'children': [],
                        'branches': [],
                        'is_head': (commit_id == self.head_commit),
                        'x': 0, 'y': 0
                    }
                
                # Add parents to queue
                for p in parents:
                    queue.append(p)
                    # We might visit p later, but we can set up reverse link now if p exists
                    # Actually, better to do post-processing for children
            except Exception as e:
                print(f"Error reading commit {commit_id}: {e}")

        # Post-process: Build children links and identify roots
        for cid, data in self.commits.items():
            if not data['parents']:
                self.root_commits.append(cid)
            for p in data['parents']:
                if p in self.commits:
                    if cid not in self.commits[p]['children']:
                        self.commits[p]['children'].append(cid)
        
        # Tag branches
        for name, cid in self.branches.items():
            if cid in self.commits:
                self.commits[cid]['branches'].append(name)

    def layout(self):
        # 1. Topological Sort / Depth Calculation (X coordinate)
        # BFS from roots
        queue = [(cid, 0) for cid in self.root_commits]
        visited = set()
        
        # To handle merges correctly (wait for all parents), we might need true topo sort.
        # But for simple visualization, depth-from-root is usually fine.
        # However, a merge commit should be at max(parent_depths) + 1.
        
        # Calculate in-degrees
        in_degree = {cid: len(data['parents']) for cid, data in self.commits.items()}
        # Only consider parents that Are in the graph
        
        ready_queue = [cid for cid, deg in in_degree.items() if deg == 0]
        
        max_x = 0
        while ready_queue:
            cid = ready_queue.pop(0)
            data = self.commits[cid]
            
            # X is 1 + max(parent.x)
            px = -1
            for p in data['parents']:
                if p in self.commits:
                    px = max(px, self.commits[p]['x'])
            data['x'] = px + 1
            max_x = max(max_x, data['x'])

            for child in data['children']:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    ready_queue.append(child)

        # 2. X coordinate scaling
        # To strictly flow Left -> Right

        # 3. Y Coordinate Assignment (Lane Allocation)
        # Heuristic:
        # - Trace paths from roots.
        # - Prefer straight lines for "main".
        # - Use branch names to prioritize lanes.
        
        # Assign 'primary_branch' to each node
        # Back-propagate branch names from tips
        # Dict: commit_id -> set of reachable branch names
        # Then pick the "best" name (e.g. main)
        
        node_branches = {cid: set(data['branches']) for cid, data in self.commits.items()}
        
        # Reverse topological order (Leaves to Roots)
        # We need a list of all nodes
        all_nodes = list(self.commits.keys())
        # Sort by X desc
        all_nodes.sort(key=lambda n: self.commits[n]['x'], reverse=True)
        
        for cid in all_nodes:
            current_branches = node_branches[cid]
            for p in self.commits[cid]['parents']:
                if p in node_branches:
                    node_branches[p].update(current_branches)
        
        # Define priority: main > master > dev > others
        def branch_priority(name):
            if name == 'main': return 100
            if name == 'master': return 99
            if name == 'dev': return 90
            if name == 'develop': return 89
            return 50

        # Assign a single 'lane_owner' branch for each node
        node_lane_ref = {} # cid -> branch_name
        for cid in self.commits:
            candidates = list(node_branches[cid])
            if not candidates:
                winner = 'detached'
            else:
                winner = max(candidates, key=branch_priority)
            node_lane_ref[cid] = winner

        # Assign Integer Y slots to branch names
        # Find all unique winner branches
        unique_refs = sorted(list(set(node_lane_ref.values())), key=branch_priority, reverse=True)
        # Center main at 0
        ref_y = {}
        # Simple stack: main=0, others alternating +1, -1, +2, -2...
        y_slots = [0]
        # Generate sequence: 0, 1, -1, 2, -2, ...
        for i in range(1, len(unique_refs) + 1):
            y_slots.append(i)
            y_slots.append(-i)
        
        for i, ref in enumerate(unique_refs):
            ref_y[ref] = y_slots[i] * 1.0 # Scale
            
        # Assign Y
        for cid in self.commits:
            ref = node_lane_ref[cid]
            self.commits[cid]['y'] = ref_y[ref]
            
        # Adjustment: Prevent collisions
        # If multiple nodes have same (x, y), shift one
        # Simple collision resolution
        position_map = {} # (x, y) -> list of cids
        for cid, data in self.commits.items():
            pos = (data['x'], data['y'])
            if pos not in position_map:
                position_map[pos] = []
            position_map[pos].append(cid)
            
        # If collision, shift Y slightly
        for pos, cids in position_map.items():
            if len(cids) > 1:
                # Sort by something deterministic (e.g. hash)
                cids.sort()
                base_y = pos[1]
                for i, cid in enumerate(cids):
                    self.commits[cid]['y'] = base_y + (i * 0.5)

    def draw(self, output_path):
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.axis('off')

        # Layout parameters
        min_x = min(d['x'] for d in self.commits.values()) if self.commits else 0
        max_x = max(d['x'] for d in self.commits.values()) if self.commits else 0
        
        # Draw Edges
        for cid, data in self.commits.items():
            x, y = data['x'], data['y']
            
            # Parents
            for pid in data['parents']:
                if pid in self.commits:
                    px, py = self.commits[pid]['x'], self.commits[pid]['y']
                    # Draw arrow from Parent to Child
                    # dx = x - px
                    # dy = y - py
                    
                    # Style based on branch
                    # If y matches, straight line. Else, curve or angled?
                    # User requested: "draw a new arrow at a 45 angle... scatter"
                    
                    arrow = patches.FancyArrowPatch((px, py), (x, y),
                                                    arrowstyle='->,head_width=0.4,head_length=0.8',
                                                    connectionstyle="arc3,rad=0.1", # slight curve
                                                    color='gray', zorder=1)
                    ax.add_patch(arrow)

        # Draw Nodes
        for cid, data in self.commits.items():
            x, y = data['x'], data['y']
            
            # Circle
            color = 'skyblue'
            if data['is_head']:
                color = 'salmon'
            
            circle = plt.Circle((x, y), 0.3, color=color, zorder=2)
            ax.add_patch(circle)
            
            # Label: Short ID
            ax.text(x, y, cid[:6], ha='center', va='center', fontsize=9, fontweight='bold', zorder=3)
            
            # Label: Branches
            if data['branches']:
                label_text = ", ".join(data['branches'])
                ax.text(x, y + 0.4, label_text, ha='center', va='bottom', fontsize=8, 
                        bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

            # Label: HEAD
            if data['is_head']:
                ax.text(x, y - 0.4, "HEAD", ha='center', va='top', fontsize=8, color='red', fontweight='bold')

        # Set limits
        if self.commits:
            ys = [d['y'] for d in self.commits.values()]
            ax.set_xlim(min_x - 1, max_x + 2)
            ax.set_ylim(min(ys) - 1, max(ys) + 1)
        
        plt.tight_layout()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path)
        print(f"Graph saved to {output_path}")

def main():
    graph = CommitGraph()
    graph.load()
    graph.layout()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join("commit_graph_images", f"graph_{timestamp}.png")
    
    graph.draw(output_path)

if __name__ == "__main__":
    main()
