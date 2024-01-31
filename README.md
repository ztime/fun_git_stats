# Fun git stats

Small script to extract some fun (but meningless) stats from git repos

It reads all commits from master/main branch and saves stats like number of insertions/deletions by hour/day etc...
saves that into a csv that you can use with `analyse_csv.py` to get some fun stats.

Install with requierments.txt

## Usage
Run `collect_repo_stats.py` first with our repos as arguments and probably `--list-users`. This will analyse the repos
and output all users, since it's very common people have several "names" in the git history.

Example:
```
python collect_repo_stats.py --repos /home/path/to/my/repo --list-users --smash-users "Jonas,jonas,ztime:Kalle,donaldduck,ducky"
```

Use `python collect_repo_stats.py --help` to get more info! 

Next, run `analyse_csv.py` on your outputted csv to get some fun stats, or use the included notebook to dig deeper!

