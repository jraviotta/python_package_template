# Minimally Sufficient Pandas Cheat Sheet
See also, [Minimally Sufficient Pandas.](https://www.dunderdata.com/post/minimally-sufficient-pandas-cheat-sheet)  
See also, [Conda Cheat Sheet](https://kapeli.com/cheat_sheets/Conda.docset/Contents/Resources/Documents/index)   
See also, [Pandas User Guide](https://pandas.pydata.org/pandas-docs/stable/user_guide/index.html)  

## Selecting Data
Use brackets to select a single column of data because the dot notation cannot column names with spaces, those that collide with DataFrame methods and when the column name is a variable.
```
df[‘colname’] # do this
df.colname    # not that
```
* Selection with `at` and `iat`  
Use NumPy arrays if your application relies on performance for selecting a single cell of data and not `at` or `iat`. The `at` and `iat` indexers give a small increase in performance when selecting a single DataFrame cell. 

* The deprecated `ix` indexer  
Every trace of `ix` should be removed and replaced with the explicit `loc` or `iloc` indexers.

## read_csv vs read_table
Use `read_csv` for all cases. The only difference between these two functions is the default delimiter.

## Data cleaning
[About pandas dtypes](https://pandas.pydata.org/pandas-docs/stable/user_guide/basics.)  
Use `convert_dtypes()` to infer dtypes  
Use `replace()` to normalize strings

## Checking for missing data
[About pandas nan](https://pandas.pydata.org/pandas-docs/stable/user_guide/missing_data.html)  
html#basics-dtypes)  
Use `isna` and `notna` as they end with ‘na’ like the other missing value methods `fillna` and `dropna`. `isna` is an alias of `isnull` and `notna` is an alias of `notnull`. 

## Arithmetic and Comparison Operators vs Methods
Use the operators( +, *, >, <=, etc..) and not their corresponding methods ( add, mul, gt, le, etc…) in all cases except when absolutely necessary such as when you need to change the direction of the alignment.

## Builtin Python functions vs Pandas methods with the same name
Use the Pandas method over any built-in Python function with the same name.

## Aggregation
* Use `df.groupby('grouping column').agg({'aggregating column': 'aggregating function'})` as it can handle more complex cases.  
* Use `gropuby` when you want to continue an analysis and `pivot_table` when you want to compare groups. A `groupby` aggregation and a `pivot_table` produce the same exact data with a different shape.  
* Only use `crosstab` when finding the relative frequency. The `pivot_table` method and the `crosstab` function are very similar.  
* Only use `pivot_table` and not `pivot`. The `pivot` method pivots data without aggregating. It is possible to duplicate its functionality with `pivot_table` by selecting an aggregation function.  
* Use `pivot_table` over `pivot` or `unstack`. `pivot_table` can handle all cases that `pivot` can, and `pivot` and `unstack` reshape data similarly.  
* Use `melt` over `stack` because it allows you to rename columns and it avoids a MultiIndex.

## Handling a MultiIndex
Flatten DataFrames after a call to `groupbyby` renaming columns and resetting the index. A DataFrame with a MultiIndex offers little benefit over one with a single-level index.


```python
df.reset_index()
# Flatten columns
df.columns = ['_'.join(col).rstrip('_') for col in df.columns.values]
```

## Setting with copy warning
https://www.dataquest.io/blog/settingwithcopywarning/

### Using `iloc` to avoid chained assignments  
No
```
data[data.bidder == 'parakeet2004']['bidderrate'] = 100
```
Yes
```
data.loc[data.bidder == 'parakeet2004', 'bidderrate'] = 100
```

### Using `.copy()` to leave underlying data untouched  
```
winners = data.loc[data.bid == data.price].copy()
winners.loc[304, 'bidder'] = 'therealname'
```
```
print(winners.loc[304, 'bidder'])
therealname
print(data.loc[304, 'bidder'])
nan
```

## Best of the DataFrame API
The minimum DataFrame attributes and methods that can accomplish nearly all data analysis tasks. It reduces the number from over 240 to less than 80.

### Attributes
```
columns
dtypes
index
shape
T
values
```

### Aggregation Methods
```
all
any
count
describe
idxmax
idxmin
max
mean
median
min
mode
nunique
sum
std
var
```

### Non-Aggretaion Statistical Methods
```
abs
clip
corr
cov
cummax
cummin
cumsum
diff
nlargest
nsmallest
quantile
rank
round
Subset Selection
head
iloc
loc
tail
```

### Missing Value Handling
```
dropna
fillna
interpolate
isna
notna
````

### Grouping
```
groupby
pivot_table
resample
rolling
```

### Joining Data
```
append
merge
```

### Other
```
asfreq
astype
copy
drop
drop_duplicates
equals
isin
melt
plot
rename
replace
reset_index
sample
select_dtypes
shift
sort_index
sort_values
to_csv
to_json
to_sql
```

### Functions
``` 
pd.concat
pd.crosstab
pd.cut
pd.qcut
pd.read_csv
pd.read_json
pd.read_sql
pd.to_datetime
pd.to_timedelta
```

# Git
https://github.com/edx/edx-platform/wiki/How-to-Rebase-a-Pull-Request

Squash your changes
This step is not always necessary, but is required when your commit history is full of small, unimportant commits (such as "Fix pep8", "Add tests", or "ARUURUGHSFDFSDFSDGLJKLJ:GK"). It involves taking all the commits you've made on your branch, and squashing them all into one, larger commit. Doing this makes it easier for you to resolve conflicts while performing the rebase, and easier for us to review your pull request.

To do this, we're going to do an interactive rebase. You can also use interactive rebase to change the wording on commit messages (for example, to provide more detail), or reorder commits (use caution here: reordering commits can cause some nasty merge conflicts).

If you know the number of commits on your branch that you want to rebase, you can simply run:

$ git rebase -i HEAD~n
where n is the number of commits to rebase.

If you don't know how many commits are on your branch, you'll first need to find the commit that is base of your branch. You can do this by running:

$ git merge-base my-branch edx/master
That command will return a commit hash. Use that commit hash in constructing this next command:

$ git rebase -i ${HASH}
Note that you should replace ${HASH} with the actual commit hash from the previous command. For example, if your merge base is abc123, you would run $ git rebase -i abc123. (Your hash will be a lot longer than 6 characters. Also, do NOT include a $!)

Perform a rebase
To rebase your branch atop of the latest version of edx-platform, run this command in your repository:

$ git rebase edx/master
Git will start replaying your commits onto the latest version of master. You may get conflicts while doing so: if you do, Git will pause and ask you to resolve the conflicts before continuing. This is exactly like resolving conflicts with a merge: you can use git status to see which files are in conflict, edit the files to resolve the conflicts, and then use git add to indicate that the conflicts have been resolved. However, instead of running git commit, you instead want to run git rebase --continue to indicate to Git that it should continue replaying your commits. If you've squashed your commits before doing this step, you'll only have to pause to resolve conflicts once -- if you didn't squash, you may have to resolve your conflicts multiple times. If you are on Git version <2.0 and you are stuck with the message "You must edit all merge conflicts and then mark them as resolved using Git add" even though you resolved and added the file, run git diff and try again.

Force-push to update your pull request
As explained above, when you do a rebase, you are changing the history on your branch. As a result, if you try to do a normal git push after a rebase, Git will reject it because there isn't a direct path from the commit on the server to the commit on your branch. Instead, you'll need to use the -f or --force flag to tell Git that yes, you really know what you're doing. When doing force pushes, it is highly recommended that you set your push.default config setting to simple, which is the default in Git 2.0. To make sure that your config is correct, run:

$ git config --global push.default simple
Once it's correct, you can just run:

$ git push -f
