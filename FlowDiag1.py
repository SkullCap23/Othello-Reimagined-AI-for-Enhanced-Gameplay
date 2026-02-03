from graphviz import Digraph

# Create a new directed graph
dot = Digraph(comment='Alpha-Beta Pruning Tree Structure', format='png')

# Root node: the initial board state with alpha and beta values
dot.node('R', 'Root Node\nα = -∞, β = +∞')

# Level 1: Two possible moves from the root
dot.node('A', 'Node A\n(Move 1)\nα = -∞, β = +∞')
dot.node('B', 'Node B\n(Move 2)\nα = -∞, β = +∞')
dot.edge('R', 'A')
dot.edge('R', 'B')

# Level 2: Expanding Node A into two child moves
dot.node('A1', 'Node A1\n(Move 1.1)\nValue = vA1')
dot.node('A2', 'Node A2\n(Move 1.2)\nValue = vA2')
dot.edge('A', 'A1')
dot.edge('A', 'A2')

# Level 2: Expanding Node B into two child moves
dot.node('B1', 'Node B1\n(Move 2.1)\nValue = vB1')
dot.node('B2', 'Node B2\n(Move 2.2)\nValue = vB2')
dot.edge('B', 'B1')
dot.edge('B', 'B2')

# Example of a pruned branch: from Node A2, we prune additional moves
dot.node('P', 'Pruned Branch\n(α ≥ β)')
dot.edge('A2', 'P', style='dotted', label='Prune')

# Optionally, you can add further nodes or annotations as needed

# Render and view the diagram (this will create a file named 'alpha_beta_tree.png')
dot.render('alpha_beta_tree', view=True)
