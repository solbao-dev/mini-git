"""Mini Git 명령줄 입력과 출력."""

import shlex

from mini_git import MiniGit


def format_commit(commit):
    """로그와 검색에 표시할 커밋 정보를 만든다."""
    time = commit.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return f"commit {commit.hash} ({commit.author}, {time})\n{commit.message}"


def _single_value(args):
    """따옴표로 묶인 공백 포함 인자를 포함해 인자 하나를 확인한다."""
    if len(args) != 1 or not args[0].strip():
        raise ValueError("Invalid args")
    return args[0]


def execute(repo, line):
    """입력 한 줄을 파싱하고 실행 결과 문자열을 반환한다."""
    try:
        parts = shlex.split(line)
    except ValueError:
        return "Invalid args"
    if not parts:
        return ""
    command, args = parts[0].upper(), parts[1:]
    try:
        if command in ("EXIT", "QUIT"):
            if args:
                raise ValueError("Invalid args")
            return None
        if command == "INIT":
            name = _single_value(args)
            repo.init(name)
            return f"Initialized repository.\nCurrent branch: main\nCurrent user: {name}"
        if command == "BRANCH":
            name = _single_value(args)
            repo.branch(name)
            return f"Created branch: {name}"
        if command == "SWITCH":
            name = _single_value(args)
            repo.switch(name)
            return f"Switched to branch: {name}"
        if command == "COMMIT":
            message = _single_value(args)
            commit = repo.commit(message)
            return f"[{repo.current_branch} {commit.hash}] {commit.message}"
        if command == "LOG":
            if not args:
                commits = repo.log()
            elif len(args) == 1 and args[0] in ("--sort-by=date", "--sort-by=author"):
                commits = repo.log(args[0].split("=", 1)[1])
            else:
                raise ValueError("Invalid args")
            return "\n".join(format_commit(commit) for commit in commits) if commits else "No commits"
        if command == "PATH":
            if len(args) != 2:
                raise ValueError("Invalid args")
            path = repo.path(args[0], args[1])
            return f"Path: {path.replace('->', ' -> ')}" if path else "No path"
        if command == "ANCESTORS":
            hash_ = _single_value(args)
            found = repo.ancestors(hash_)
            return "\n".join(found) if found else "No ancestors"
        if command == "SEARCH":
            value = _single_value(args)
            if value.startswith("--author="):
                author = value[len("--author="):]
                if not author:
                    raise ValueError("Invalid args")
                matches = repo.search_author(author)
            elif value.startswith("--"):
                raise ValueError("Invalid args")
            else:
                matches = repo.search_keyword(value)
            if not matches:
                return "Found 0 commits."
            return f"Found {len(matches)} commit(s):\n" + "\n".join(
                f"- {commit.hash}: {commit.message}" for commit in matches
            )
        return "Unknown command"
    except ValueError as error:
        return str(error)


def main():
    """종료 명령이나 입력 종료까지 REPL을 반복한다."""
    repo = MiniGit()
    while True:
        try:
            line = input("mini-git> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        result = execute(repo, line)
        if result is None:
            break
        if result:
            print(result)


if __name__ == "__main__":
    main()
