# Wikipedia example:
#   1 2 3 4 5 6 7
# A 1 0 0 1 0 0 1
# B 1 0 0 1 0 0 0
# C 0 0 0 1 1 0 1
# D 0 0 1 0 1 1 0
# E 0 1 1 0 0 1 1
# F 0 1 0 0 0 0 1

# Choose column with lowest number of 1s (column 1)
# Select row A, remove it and all rows and columns where there is a 1 in the same position as row A:
#   2 3 5 6
# D 0 1 1 1
# Lowest number of 1s is column 2, but it is 0, thus this branch terminates unsuccessfully

# Select row B:
#   2 3 5 6 7
# D 0 1 1 1 0
# E 1 1 0 1 1
# F 1 0 0 0 1

# Lowest number of 1s is column 5
# Select row D:
#   2 7
# F 1 1

# Select row F:
# Matrix is empty, hence this branch terminates successfully. Rows B, D, and F are returned as the solution.

from abc import ABC
from typing import List, Optional, Tuple


class NodeBase(ABC):
    def __init__(
        self,
        val,
        row: int,
        col: int,
        left: Optional['NodeBase']=None,
        right: Optional['NodeBase']=None,
        up: Optional['NodeBase']=None,
        down: Optional['NodeBase']=None
    ) -> None:
        self.val = val
        self.row = row
        self.col = col
        self.left = left
        self.right = right
        self.up = up
        self.down = down
        self.removed = False


    def __repr__(self) -> str:
        return f'{self.val} ({self.row}, {self.col})'


class ColumnHeaderNode(NodeBase):
    def __repr__(self) -> str:
        return f'CH {super().__repr__()}'


class HeadNode(NodeBase):
    def __repr__(self) -> str:
        return f'H {super().__repr__()}'


class Node(NodeBase):
    def __init__(
        self,
        val,
        row: int,
        col: int,
        col_header: ColumnHeaderNode,
        left: Optional['NodeBase']=None,
        right: Optional['NodeBase']=None,
        up: Optional['NodeBase']=None,
        down: Optional['NodeBase']=None
    ) -> None:
        super().__init__(val, row, col, left=left, right=right, up=up, down=down)
        self.col_header = col_header


    def __repr__(self) -> str:
        return f'N {super().__repr__()}'


def printnodematrix(node_matrix: HeadNode, n_rows: int, n_cols: int) -> None:
    '''
    Prints the node matrix.
    '''
    res = [['+' for _ in range(n_cols)] for _ in range(n_rows)]
    
    # traverse node_matrix column by column
    current_col = node_matrix.right
    while current_col != node_matrix:
        current_node = current_col.down
        while current_node != current_col:
            res[current_node.row][current_node.col] = '1'
            current_node = current_node.down
        current_col = current_col.right

    print(' '.join(map(str, range(n_cols))) + '\n' + '\n'.join([' '.join(map(str, row)) for row in res]))


def createnodematrix(comp_mat: List[List[int]], n_rows: int, n_cols: int) -> HeadNode:
    '''
    Creates a node representation of the given compressed matrix. Every node is connected to the 4
    adjacent nodes. The connections are circular. Returns the head node.
    '''
    head = HeadNode('h', 0, 0)
    prev = head

    # create column header nodes
    heads = [ColumnHeaderNode(0, 0, 0) for _ in range(n_cols)]
    tails = [col_head for col_head in heads]
    for col_node in heads:
        col_node.left = prev
        prev.right = col_node
        prev = col_node
    head.left = prev
    prev.right = head

    # create matrix of nodes row by row
    for row_num in range(n_rows):
        row_head = None
        row_tail = None
        for col in comp_mat[row_num]:
            node = Node(val=1, row=row_num, col=col, col_header=heads[col])

            # link new node to its column
            node.up = tails[col]
            tails[col].down = node
            tails[col] = node
            node.col_header.val += 1

            if row_head is None:
                row_head = node
            if row_tail:  # link new node to the previous node created
                node.left = row_tail
                row_tail.right = node
            row_tail = node

        # wrap the row around if any nodes were created
        if row_head is not None:
            row_head.left = row_tail
            row_tail.right = row_head

    # wrap the tails of each column back to their heads
    for col in range(n_cols):
        tails[col].down = heads[col]
        heads[col].up = tails[col]

    return head


def exactcover(node_matrix: HeadNode, partial_solution: List[Node]=[], all_solutions: List[Node]=[]) -> List[List[Node]]:
    '''
    Finds a subset of rows from the node matrix which solves the exact cover problem or None if no
    solution is found.
    '''
    selected_col, selected_count = selectcol(node_matrix)
    if selected_col == node_matrix:  # empty matrix, partial solution is a complete solution
        all_solutions.append(partial_solution[:])
        # return partial_solution
        return

    # if the column has no '1's, an exact cover is impossible
    if selected_count == 0:
        return

    # iterate through the rows which are '1's
    current_row = selected_col.down
    while current_row != selected_col:  # current_row guaranteed != header node

        # include current row in partial solution
        partial_solution.append(current_row)

        # iterate each column in current row
        deleted_nodes = []
        deleting_col = current_row
        while True:
            # iterate each row in that column
            deleting_row = deleting_col
            while True:
                if type(deleting_row) == Node: # skip header rows
                    deleted_nodes += removerow(deleting_row)

                if deleting_row.down == deleting_row:
                    break
                deleting_row = deleting_row.down

            deleted_nodes += removecolumn(deleting_col)

            if deleting_col.right == deleting_col:
                break
            deleting_col = deleting_col.right

        # recurse with the reduced dancing links
        exactcover(node_matrix, partial_solution, all_solutions)
        # if ret is not None:
        #     return ret

        # restore state before moving on
        partial_solution.pop()
        for node in deleted_nodes:
            restorenode(node)

        current_row = current_row.down
    
    # no solution was found
    return


def selectcol(node_matrix: HeadNode) -> Tuple[ColumnHeaderNode, int]:
    '''
    Selects the column with the fewest number of nodes.
    '''
    current = node_matrix.right
    selected_col = node_matrix.right
    selected_count = None
    while current != node_matrix:
        if selected_count is None or current.val < selected_count:
            selected_col = current
            selected_count = current.val
            if selected_count == 0:  # terminate early if empty column is found
                return selected_col, selected_count
        current = current.right
    return selected_col, selected_count


def removecolumn(node_in_column: Node) -> List[Node]:
    '''Removes a column of nodes and returns them in order of their removal'''
    current = node_in_column
    removed_nodes = []
    while True:
        if not current.removed:
            removed_nodes.append(removenode(current))
        if current.down == current:  # linking to itself, means entire column is removed
            return removed_nodes
        current = current.down


def removerow(node_in_row: Node) -> List[Node]:
    '''Removes a row of nodes and returns them in order of their removal'''
    current = node_in_row
    removed_nodes = []
    while True:
        if not current.removed:
            removed_nodes.append(removenode(current))
        if current.right == current:  # linking to itself, means entire row is removed
            return removed_nodes
        current = current.right


def removenode(node: Node) -> Node:
    '''Idempotently remove node'''
    if node.removed:
        return node
    node.left.right = node.right
    node.right.left = node.left
    node.up.down = node.down
    node.down.up = node.up
    if type(node) == Node:
        node.col_header.val -= 1
    node.removed = True
    return node


def restorenode(node: Node) -> Node:
    '''Idempotently restore node'''
    if not node.removed:
        return node
    node.left.right = node
    node.right.left = node
    node.up.down = node
    node.down.up = node
    if type(node) == Node:
        node.col_header.val += 1
    node.removed = False
    return node


if __name__ == '__main__':
    def compressmat(mat):
        comp_mat = []
        for r in mat:
            row = []
            for i, n in enumerate(r):
                if n == 1:
                    row.append(i)
            comp_mat.append(row)
        return comp_mat
    mat = [
        [1,0,0,1,0,0,1],
        [1,0,0,1,0,0,0],
        [0,0,0,1,1,0,1],
        [0,0,1,0,1,1,0],
        [0,1,1,0,0,1,1],
        [0,1,0,0,0,0,1]
    ]
    comp_mat = [
        [0,3,6],
        [0,3],
        [3,4,6],
        [2,4,5],
        [1,2,5,6],
        [1,6]
    ]  # this is the compressed version of the matrix above that will be used
    n_rows = len(mat)
    n_cols = len(mat[0])

    node_matrix = createnodematrix(compressmat(mat), n_rows, n_cols)
    printnodematrix(node_matrix, n_rows=n_rows, n_cols=n_cols)

    ret = []
    exactcover(node_matrix, all_solutions=ret)
    print(ret)
