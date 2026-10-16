# Mini Git

## 프로젝트 소개와 목표

파일 내용 대신 **커밋 메타데이터**를 메모리에 기록하는 작은 Git 학습 프로그램입니다. 코디세이 5-2 필수 미션의 브랜치, 커밋 DAG, 부모 우선 로그, 그래프 탐색, 역색인 검색, 직접 구현한 정렬을 확인할 수 있습니다.

## 개발 환경과 구조

- Python 3.10 이상, 표준 라이브러리만 사용
- `main.py`: REPL, 명령어 파싱과 출력
- `mini_git.py`: `Commit`, `MiniGit`, 브랜치·커밋 해시맵·역색인
- `algorithms.py`: 위상 탐색, BFS 최단 경로, 조상 탐색, Merge Sort
- `tests/test_mini_git.py`: `unittest` 자동 테스트
- `.gitignore`: 원문 자료, Python 임시 파일, 환경변수 파일 제외

## 실행 방법

프로젝트 폴더에서 실행합니다.

```bash
python3 main.py
```

`mini-git>` 프롬프트가 나타나면 명령어를 입력합니다. `exit` 또는 `quit`로 종료합니다. 모든 데이터는 실행 중에만 메모리에 보관됩니다.

## 전체 명령어

| 명령어 | 동작 |
| --- | --- |
| `INIT <user_name>` | 저장소와 빈 `main` 브랜치 생성, 작성자 설정 |
| `BRANCH <branch_name>` | 현재 브랜치가 가리키는 커밋에서 새 브랜치 생성 |
| `SWITCH <branch_name>` | 현재 브랜치 전환 |
| `COMMIT <message>` | 현재 브랜치에 커밋 추가, 해시 출력 |
| `LOG` | 모든 브랜치의 커밋을 부모 우선으로 출력 |
| `LOG --sort-by=date` | 날짜 오름차순, 같은 시각은 해시 오름차순 |
| `LOG --sort-by=author` | 작성자 오름차순, 같은 작성자는 해시 오름차순 |
| `PATH <commit1> <commit2>` | 무방향 연결의 최단 경로 출력 |
| `ANCESTORS <commit_hash>` | 자기 자신을 제외한 모든 조상 출력 |
| `SEARCH <keyword>` | 메시지 단어로 검색 |
| `SEARCH --author=<name>` | 작성자 이름으로 검색 |
| `exit`, `quit` | 프로그램 종료 |

명령어 자체는 대소문자를 구분하지 않습니다. 사용자명과 브랜치명은 대소문자를 구분하고, 메시지의 대소문자는 원형 그대로 저장합니다. 키워드 검색은 `lower()`로 정규화하므로 대소문자를 구분하지 않습니다. 작성자 검색은 대소문자를 구분합니다. 공백이 포함된 인자는 따옴표로 묶습니다. 메시지 키워드는 `split()`으로 나눈 완전한 토큰에 매치되며 부분 문자열 검색은 아닙니다. `SEARCH "login feature"`처럼 여러 단어를 입력하면 **모든 단어를 포함한** 커밋을 역색인 교집합으로 찾습니다. 잘못된 인자나 옵션은 `Invalid args`, 없는 브랜치와 커밋은 `Unknown branch: ...`, `Unknown commit: ...`로 알려줍니다. 초기화 전 명령은 `Repository not initialized`로 알려줍니다.

## 평가 시연

아래 순서대로 입력하면 커밋 해시는 세션의 증가 카운터에 따라 `000001`, `000002`, `000003`으로 나옵니다. 출력의 시각은 실제 실행 시각입니다.

```text
mini-git> INIT "Alice"
Initialized repository.
Current branch: main
Current user: Alice
mini-git> COMMIT "Initial commit"
[main 000001] Initial commit
mini-git> BRANCH feature
Created branch: feature
mini-git> SWITCH feature
Switched to branch: feature
mini-git> COMMIT "Add login feature"
[feature 000002] Add login feature
mini-git> SWITCH main
Switched to branch: main
mini-git> COMMIT "Add payment feature"
[main 000003] Add payment feature
mini-git> PATH 000002 000003
Path: 000002 -> 000001 -> 000003
mini-git> ANCESTORS 000002
000001
mini-git> SEARCH login
Found 1 commit(s):
- 000002: Add login feature
mini-git> SEARCH --author=Alice
Found 3 commit(s):
...
mini-git> LOG
commit 000001 (Alice, 실제 실행 시각)
Initial commit
commit 000002 (Alice, 실제 실행 시각)
Add login feature
commit 000003 (Alice, 실제 실행 시각)
Add payment feature
mini-git> LOG --sort-by=date
...
mini-git> LOG --sort-by=author
...
mini-git> quit
```

다른 순서로 커밋했다면 `COMMIT` 결과에 표시된 **실제 해시**를 `PATH`에 입력하세요. `LOG`에서는 각 커밋의 해시, 작성자, 시각, 메시지를 확인할 수 있습니다.

## 설명 자료

1. **DAG와 커밋 그래프:** DAG는 화살표 방향으로 따라가도 출발점으로 돌아오지 않는 그래프입니다. 각 커밋은 부모 해시를 가리키며, 새 커밋은 이미 존재하는 부모만 참조합니다. 이력의 분기와 부모 관계를 나타내기 위해 그래프를 씁니다. `Commit`, `MiniGit.create_commit`에 구현했습니다. 일반 `COMMIT`은 부모가 0개 또는 1개이며, 내부 자료구조는 여러 부모도 표현합니다.
2. **부모 우선 LOG:** 각 커밋의 부모 수를 세고 부모 수가 0인 커밋부터 꺼냅니다. 부모를 출력할 때 자식의 남은 부모 수를 줄이고, 0이 되면 출력 대기열에 넣습니다. 모든 부모가 자식보다 앞서는 위상 정렬입니다. `algorithms.parent_first`, `MiniGit.log`를 보세요.
3. **BFS 최단 경로:** 부모 연결을 양방향으로 만들고 BFS로 한 간선씩 넓혀 가면 처음 얻은 거리가 최소 간선 수입니다. 같은 길이의 경로에서는 `hash1->hash2->...` **전체 문자열**을 비교해 사전순 최소를 고릅니다. `algorithms.shortest_path`, `MiniGit.path`입니다. 연결이 없으면 `No path`입니다.
4. **조상 탐색:** 시작 커밋의 부모부터 스택으로 계속 따라갑니다. 방문 집합이 중복을 막고, 시작 커밋은 결과에서 제외합니다. `algorithms.ancestors`, `MiniGit.ancestors`입니다.
5. **역색인:** 커밋 생성 시 `메시지 단어 → 해시 목록`, `작성자 → 해시 목록`을 만듭니다. 검색에서는 인덱스에 해당하는 해시만 읽으므로 모든 커밋을 매번 검사하지 않습니다. 전체 순회는 커밋 수를 `n`이라 할 때 O(n)이고, 단일 단어 또는 작성자 검색은 평균 O(1) 조회에 해당 목록 길이 `k`만큼의 O(k)가 더해집니다. 여러 단어 검색은 각 목록을 교집합으로 검사하므로 관련 목록 길이에 비례합니다. `MiniGit._index_commit`, `search_keyword`, `search_author`입니다.
6. **Merge Sort:** 목록을 절반으로 나눠 각 절반을 정렬하고, 작은 항목부터 두 절반을 합칩니다. 평균과 최악 모두 O(n log n)이며 추가 공간은 O(n)입니다. 키가 같을 때 왼쪽 항목을 먼저 합치므로 원래 순서를 유지하는 **안정 정렬**입니다. `algorithms.merge_sort`를 날짜와 작성자 정렬에 재사용합니다. 실제 `LOG`는 동률의 결과를 일정하게 하려고 `(시각, 해시)` 또는 `(작성자, 해시)`를 키로 사용합니다.

## 자동 테스트

```bash
python3 -m unittest discover -s tests -v
```

실제 실행 결과: **29개 테스트 실행, 성공 29개, 실패 0개** (`Ran 29 tests ... OK`). 브랜치 분기, 다중 부모 DAG, 부모 우선 로그, 정렬, BFS의 무방향·최단 경로·전체 문자열 사전순 동률, 조상 중복 제거, 역색인, CLI 오류와 종료, 금지된 정렬 API 미사용을 검증합니다.

## 구현 범위

커밋은 현재 세션에서만 유지되고 프로그램을 다시 시작하면 해시가 `000001`부터 시작합니다. `MERGE` 명령어는 없지만 커밋 자료구조의 `parents`는 0개 이상의 부모를 저장할 수 있습니다.
