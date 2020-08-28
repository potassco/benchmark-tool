"""
   
http://stackoverflow.com/questions/6575058/tarjans-strongly-connected-components-algorithm-in-python-not-working

"""
import itertools

def strong_connect(vertex,edges):
    global  indices, lowlinks, connected_components, index, stack
    indices[vertex] = index
    lowlinks[vertex] = index
    index += 1
    stack.append(vertex)

    for v, w in (e for e in edges if e[0] == vertex):
        if indices[w] < 0:
            strong_connect(w,edges)
            lowlinks[v] = min(lowlinks[v], lowlinks[w])
        elif w in stack:
            lowlinks[v] = min(lowlinks[v], indices[w])

    if indices[vertex] == lowlinks[vertex]:
        connected_components.append([])
        while stack[-1] != vertex:
            connected_components[-1].append(stack.pop())
        connected_components[-1].append(stack.pop())
        
    return connected_components

def scc(edges):
    global indices, lowlinks, connected_components, index, stack
    vertices = set(v for v in itertools.chain(*edges))
    indices = dict((v, -1) for v in vertices)
    lowlinks = indices.copy()
    connected_components = []
    index = 0
    stack = []
    for v in vertices:
        if indices[v] < 0:
            strong_connect(v,edges)
    return connected_components
    
if __name__ == '__main__':


    edges = [('A', 'B'), ('B', 'C'), ('D', 'E'), ('E', 'A'), ('C', 'E'), ('D', 'F'), ('F', 'B'), ('E', 'F')]
    edges = [('B', 'A'), ('B', 'C'), ('C', 'B'), ('C', 'A')]
    
    
    print(scc(edges))

