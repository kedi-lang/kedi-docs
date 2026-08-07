# Installation and Registries

Kedi installs package source into a user-local registry. Installation validates
the manifest, Python compatibility, source containment, file kinds, and bounded
tree size before replacing an existing installed copy.

## Install a Local Package

From a package root:

```console
$ kedi install
Installed kedi_http ...
```

Or identify the manifest:

```console
$ kedi install path/to/package.kedi
```

The command copies `package.kedi` and its declared source directory. It does not
install `python_dependencies`.

Installing the same package name replaces the previous installation as one
validated transaction. Do not edit installed registry files manually; reinstall
from a source package.

## Add a Named Package

```console
$ kedi add package_name
```

Named add uses the `registry.kedi-lang.org/v1/package/<name>` contract. If no
registry is configured or available in the current release, the command fails
clearly rather than guessing a source.

For local registry-contract testing, set `KEDI_REGISTRY_MOCK_ROOT` to a directory
whose children are package source directories:

```console
$ export KEDI_REGISTRY_MOCK_ROOT=/absolute/path/to/mock-registry
$ kedi add kedi_http
```

The mock path is development infrastructure, not a production trust mechanism.

## Add an Explicit GitHub Package

```console
$ kedi add git+https://github.com/user/project.git
```

Kedi accepts credential-free `https` URLs hosted on `github.com`. It performs a
shallow, no-checkout clone with blob filtering, reads the root `package.kedi`,
and sparse-checks out only the declared source tree. The checked-out commit is
printed and recorded.

Arbitrary hosts, embedded credentials, unsafe source patterns, manifest
symlinks, and files escaping the checkout are rejected. A Git URL is an explicit
source install; it is separate from future registry release resolution.

## Registry Location

The default home is:

```text
~/.kedi/
  registry/
    kedi_http/
      package.kedi
      .kedi-install.json
      src-or-copied-source...
```

Set `KEDI_HOME` to move all Kedi-owned state:

```console
$ export KEDI_HOME=/absolute/path/to/kedi-home
```

The override must be absolute. Relative values are rejected so changing the
working directory cannot silently switch registries.

## Installation Receipts

Each installed package has `.kedi-install.json` containing Kedi-owned provenance
such as source kind, source path, manifest digest, and, for Git, normalized URL
and commit. The receipt supports diagnosis and integrity checks; it is not a
signature or security audit.

Do not publish a source-owned `.kedi-install.json` and do not treat receipt
fields as package-controlled metadata.

## Source Safety and Limits

Installation accepts regular files and directories within the declared source
tree. It rejects path traversal, symlink escapes, special files, sparse-checkout
patterns, missing `main.kedi`, and trees exceeding configured count or size
bounds.

Installed-package resolution repeats boundary checks. It rejects a symlinked
package root or manifest, a directory name that disagrees with the manifest,
missing metadata, and source files outside the package.

These checks protect the registry layout and installation transaction. They do
not make package code safe to execute.

## Executable-Code Security

Importing a third-party Kedi package can execute its prelude, Python blocks, and
top-level statements with the Kedi process's host permissions. Review the exact
source and commit, install in an isolated Python environment, and restrict host
credentials and filesystem access as you would for any Python dependency.

A registry-verified commit establishes identity and integrity. It does not
sandbox behavior, prove correctness, or approve capabilities.
