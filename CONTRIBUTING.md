# Contributing to tattler

Thank you for considering donating some of your time and talent to the benefit of the community!

Here's some practical guidelines to maximize the chance that your contribution can be integrated into the project.


# Ways to contribute

- [Report an issue](#report-an-issue) and make it actionable for developers
- [Suggest enhancements](#suggest-enhancements) and make their benefit clear
- [Contribute code](#contribute-code) so it's compatible and can be maintained


## Report an issue

Do so on [tattler's issue tracker](https://github.com/tattler-community/tattler-community/issues).

Cover the following when describing an issue:

1. What version of tattler are you reporting this issue for?
1. What is the behavior you have issue with?
1. What behavior would you expect instead?
1. What is the impact of the issue?
1. How severe is this impact (low, medium, high)?


## Suggest enhancements

Do so on [tattler's issue tracker](https://github.com/tattler-community/tattler-community/issues).

Cover the following when describing your proposal:

1. What is the general idea?
1. How could it look like concretely in tattler's functionality?
1. What makes this idea worth the extra complexity it costs?


## Contribute code

We welcome code contributions for [reported issues](https://github.com/tattler-community/tattler-community/issues) and
are selectively open to code contributions for [suggested enhancements](https://github.com/tattler-community/tattler-community/issues).

We may decline contributions in a number of scenarios:

- The contribution breaks some of [tattler's design principles](#tattlers-design-principles).
- The contribution breaks one of the contributing rules below.
- The contribution adds too much complexity for the value it adds.
- The contribution reduces code coverage by too much, forcing our developers to spend time writing the tests for your code that you did not care to write.

Proceed as follows to contribute code:

1. [Write an issue](#report-an-issue) in tattler's issue tracker.
1. Fork tattler's repository.
1. Create a branch in your forked repository to address the issue.
1. Create a merge request in tattler's repository describing what you changed.


### Tattler's design principles

- Stay easy to use.
- Prevent any advanced feature from making a basic features harder to use.
- An insufficiently documented feature is a broken feature.
- If some lines of code require no test coverage, does tattler require those lines in its codebase?
- Comments are more expensive to maintain than code, so rather write code that requires no comments.
- When it comes to optimization -- "slow is smooth, and smooth is fast".


### Contributing rules

- All code and documentation in English. This includes symbol names and comments.
- The testing pipeline must pass upon your changes.
- You may reduce code coverage of the files you change by no more than 5%.
- Every addition or modification of functionality must be documented.
