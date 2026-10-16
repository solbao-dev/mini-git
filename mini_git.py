"""메모리 안에서 동작하는 Mini Git 저장소."""

from dataclasses import dataclass
from datetime import datetime

from algorithms import ancestors, merge_sort, parent_first, shortest_path


@dataclass(frozen=True)
class Commit:
    """커밋의 메타데이터와 이미 존재하는 부모 커밋의 해시를 보관한다."""

    hash: str
    message: str
    author: str
    timestamp: datetime
    parents: tuple[str, ...]


class MiniGit:
    """브랜치, 커밋 해시맵, 작성자·키워드 역색인을 관리한다."""

    def __init__(self, clock=None):
        self.clock = clock or datetime.now
        self.commits = {}
        self.branches = {}
        self.current_branch = None
        self.author = None
        self.keyword_index = {}
        self.author_index = {}
        self.next_hash = 1

    def require_init(self):
        """초기화 전 명령을 명확한 오류로 바꾼다."""
        if self.current_branch is None:
            raise ValueError("Repository not initialized")

    def init(self, user_name):
        """작성자를 등록하고 빈 main 브랜치로 저장소를 시작한다."""
        if self.current_branch is not None:
            raise ValueError("Repository already initialized")
        self.author = user_name
        self.branches["main"] = None
        self.current_branch = "main"

    def branch(self, name):
        """현재 브랜치의 끝 커밋을 가리키는 새 브랜치를 만든다."""
        self.require_init()
        if name in self.branches:
            raise ValueError(f"Branch already exists: {name}")
        self.branches[name] = self.branches[self.current_branch]

    def switch(self, name):
        """존재하는 브랜치로 현재 위치를 바꾼다."""
        self.require_init()
        if name not in self.branches:
            raise ValueError(f"Unknown branch: {name}")
        self.current_branch = name

    def _index_commit(self, commit):
        """메시지 토큰과 작성자로 커밋 해시를 찾을 수 있게 등록한다."""
        self.author_index.setdefault(commit.author, []).append(commit.hash)
        for word in set(token.lower() for token in commit.message.split()):
            self.keyword_index.setdefault(word, []).append(commit.hash)

    def create_commit(self, message, parents):
        """기존 부모만 받아 새 커밋을 만들어 DAG와 역색인을 갱신한다."""
        self.require_init()
        if not message.strip() or len(parents) != len(set(parents)):
            raise ValueError("Invalid args")
        for parent in parents:
            self.get_commit(parent)
        hash_ = f"{self.next_hash:06x}"
        self.next_hash += 1
        commit = Commit(hash_, message, self.author, self.clock(), tuple(parents))
        self.commits[hash_] = commit
        self._index_commit(commit)
        return commit

    def commit(self, message):
        """현재 브랜치의 끝을 부모로 새 커밋을 만들고 브랜치를 이동한다."""
        self.require_init()
        head = self.branches[self.current_branch]
        created = self.create_commit(message, [head] if head else [])
        self.branches[self.current_branch] = created.hash
        return created

    def get_commit(self, hash_):
        """해시맵으로 커밋을 조회하고 없으면 오류를 알린다."""
        self.require_init()
        if hash_ not in self.commits:
            raise ValueError(f"Unknown commit: {hash_}")
        return self.commits[hash_]

    def log(self, sort_by=None):
        """기본 로그는 부모 우선, 정렬 옵션은 병합 정렬로 반환한다."""
        self.require_init()
        ordered = parent_first(self.commits)
        if sort_by == "date":
            return merge_sort(ordered, key=lambda c: (c.timestamp, c.hash))
        if sort_by == "author":
            return merge_sort(ordered, key=lambda c: (c.author, c.hash))
        if sort_by is not None:
            raise ValueError("Invalid args")
        return ordered

    def path(self, start, end):
        """두 해시를 검증한 뒤 BFS 기반 최단 경로 문자열을 구한다."""
        self.get_commit(start)
        self.get_commit(end)
        return shortest_path(self.commits, start, end)

    def ancestors(self, hash_):
        """해당 커밋의 중복 없는 조상을 부모 우선 순서로 반환한다."""
        self.get_commit(hash_)
        return ancestors(self.commits, hash_)

    def search_keyword(self, word):
        """각 단어의 역색인 교집합에서 일치하는 커밋을 찾는다."""
        self.require_init()
        words = word.lower().split()
        if not words:
            return []
        candidates = self.keyword_index.get(words[0], [])
        other_matches = [set(self.keyword_index.get(token, [])) for token in words[1:]]
        return [self.commits[hash_] for hash_ in candidates
                if all(hash_ in matches for matches in other_matches)]

    def search_author(self, name):
        """대소문자를 구별하는 작성자 역색인에서 커밋을 찾는다."""
        self.require_init()
        return [self.commits[hash_] for hash_ in self.author_index.get(name, [])]
