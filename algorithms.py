"""Mini Git에서 사용하는 그래프 탐색과 직접 구현한 정렬 알고리즘."""

from collections import deque


def merge_sort(items, key):
    """병합 정렬로 새 목록을 반환한다. 같은 키는 입력 순서를 유지한다."""
    if len(items) < 2:
        return list(items)
    middle = len(items) // 2
    left = merge_sort(items[:middle], key)
    right = merge_sort(items[middle:], key)
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def parent_first(commits):
    """진입 차수 기반 위상 탐색으로 모든 부모를 자식보다 먼저 반환한다."""
    children = {hash_: [] for hash_ in commits}
    degree = {hash_: 0 for hash_ in commits}
    for commit in commits.values():
        for parent in commit.parents:
            children[parent].append(commit.hash)
            degree[commit.hash] += 1
    queue = deque(hash_ for hash_, count in degree.items() if count == 0)
    result = []
    while queue:
        hash_ = queue.popleft()
        result.append(commits[hash_])
        for child in children[hash_]:
            degree[child] -= 1
            if degree[child] == 0:
                queue.append(child)
    if len(result) != len(commits):
        raise ValueError("Commit graph contains a cycle")
    return result


def ancestors(commits, start):
    """부모 방향으로 탐색해 시작 커밋을 제외한 모든 조상을 찾는다."""
    found = set()
    stack = list(commits[start].parents)
    while stack:
        hash_ = stack.pop()
        if hash_ == start or hash_ in found:
            continue
        found.add(hash_)
        stack.extend(commits[hash_].parents)
    return [commit.hash for commit in parent_first(commits) if commit.hash in found]


def shortest_path(commits, start, end):
    """무방향 BFS 최단 거리 후 전체 경로 문자열이 최소인 경로를 반환한다."""
    neighbors = {hash_: set() for hash_ in commits}
    for commit in commits.values():
        for parent in commit.parents:
            neighbors[commit.hash].add(parent)
            neighbors[parent].add(commit.hash)

    distance = {start: 0}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for neighbor in neighbors[current]:
            if neighbor not in distance:
                distance[neighbor] = distance[current] + 1
                queue.append(neighbor)
    if end not in distance:
        return None

    # 거리 증가 방향의 간선만 고르면 최단 경로만 남고 순환도 사라진다.
    choices = {end: end}

    def best_from(current):
        """현재 정점에서 끝까지 이어지는 사전순 최소 문자열을 구한다."""
        if current in choices:
            return choices[current]
        candidates = []
        for neighbor in neighbors[current]:
            if distance.get(neighbor) == distance[current] + 1:
                suffix = best_from(neighbor)
                if suffix is not None:
                    candidates.append(current + "->" + suffix)
        choices[current] = min(candidates) if candidates else None
        return choices[current]

    return best_from(start)
