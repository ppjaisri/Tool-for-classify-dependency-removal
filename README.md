# Tool for classifying dependency remvoal scenaio

The purpose of this tool is to classify dependency removal scenarios on the NPM ecosystem.

The dependency removal scenario is the sequence of commit in project since initially install a dependency until remove it from the project. <br>

- **Dependency Removals with Direct Code Impact**: <br>
    Dependency removal scenarios where a dependency is removed alongside with the code modification, indicating that the removal directly affects the source code (i.e. remove the dependency from the `package.json` with code changes in a commit).
- **Dependency Removals without Direct Code Impact**: <br>
    An opposite of a previous type which refers to dependency removal scenarios where a dependency is removed without the code modification, indicating that the removal is not directly affects the source code (i.e. remove the dependency from the `package.json` only).
- **Unknown**: <br>
    Cannot determine the reason for dependency removal.