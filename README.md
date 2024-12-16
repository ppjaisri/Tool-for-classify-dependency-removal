# Tool for classifying dependency remvoal scenaio

The purpose of this tool is to classifying the dependency removal scenario.
For the current version is support only the project on NPM.

The dependency removal scenario is the sequence of commit in project since initially install a dependency until remove it from the project. <br>
Each scenario is based on 6 categories of dependency removal which have been proposed in the thesis <br>
[An Empirical Study on Removing Library Dependencies for Open Source Libraries](https://naist.repo.nii.ac.jp/record/2000600/files/R019234.pdf).

- **Replace dependency with functions**: <br>
    Replace the removed dependency with built-ins functions, functions or features from built-ins dependency (i.e. standard libraries), or custom functions.
- **Replace dependency with another dependency**: <br>
    Replace the removed dependency with another dependency or other dependencies which their feature are related to the removed dependency.
- **Remove bloat dependency**: <br>
    Remove dependencies from the list of dependencies only without remove any code from the project.
- **Shrink library**: <br>
    Remove dependencies from the list of dependencies and their features from the project.
- **Move dependency to other fields**: <br>
    Move dependencies from the field dependencies to other fields (eg. devDependencies, optionalDependencies, etc.)
- **Unknown**: <br>
    Cannot determine the reason for dependency removal.