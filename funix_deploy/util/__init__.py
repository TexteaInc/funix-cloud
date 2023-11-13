def is_git_url(s: str | None) -> bool:
    if s is None:
        return False

    # ad hoc check
    if "github.com" in s:
        return True

    if s.startswith("https://") and s.endswith(".git"):
        return True

    if s.startswith("git@") and s.endswith(".git"):
        return True

    return False
