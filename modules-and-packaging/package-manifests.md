# Package Manifests

`package.kedi` is a declarative package manifest written in Kedi directive
syntax. It is not an executable module.

## Complete Manifest

```kedi
> package: kedi_http:
  version: 1.2.0
  source: src/kedi_http
  python: python@3.11-3.14
  python_dependencies:
    httpx>=0.27
    pydantic>=2
```

The file must be named exactly `package.kedi` and contain exactly one package
directive. Comments are allowed; imports, exports, procedures, custom types,
Python blocks, assignments, and other executable statements are rejected.

## Package Name

Package names use lowercase ASCII letters, digits, and underscores, start with a
letter, and match the installed registry directory:

```text
kedi_http    valid
http2        valid
KediHTTP     invalid
kedi-http    invalid
2http        invalid
```

The package name is also the root module name used by importers.

## Version

`version` is optional but, when present, must be a valid PEP 440 version:

```kedi
> package: reports:
  version: 2.0.0rc1
  source: src/reports
```

The manifest version is package metadata. It does not select a Python
environment or automatically enforce API compatibility between packages.

## Source Directory and `main.kedi`

`source` is required for installation. It is a literal relative directory
inside the package root and must contain `main.kedi`:

```text
package.kedi
src/
  kedi_http/
    main.kedi
    client.kedi
```

For `source: src/kedi_http`, `> import: kedi_http` loads `main.kedi` and
`> import: kedi_http/client` loads `client.kedi`.

Absolute paths, parent traversal, symlink escapes, sparse-checkout metacharacters
such as `*`, missing directories, and a source without `main.kedi` are rejected.

## Python Version Requirement

The optional `python` field accepts only:

```text
python@3.11
python@3.11-3.14
```

The range is closed and inclusive. The upper version cannot precede the lower
version. Installation checks the interpreter running the installer and refuses
an incompatible package.

This field expresses host compatibility, not a dependency to install.

## Python Dependencies

`python_dependencies` is an indented list of PEP 508 requirement strings:

```kedi
> package: reports:
  source: src/reports
  python_dependencies:
    pydantic>=2
    httpx[http2]>=0.27; python_version >= "3.11"
```

Kedi validates each requirement string but does not install it into the active
environment. Package authors must document or provide the environment setup
that satisfies these dependencies. Use the bundled `require` module for a clear
runtime check when an optional feature needs a package.

## Unknown and Duplicate Fields

Supported fields are `version`, `source`, `python`, and
`python_dependencies`. Unknown fields, duplicate scalar fields, multiple
dependency blocks, multiple package directives, and a missing package directive
are errors.

Manifest validation happens before installation and again when an installed
package is resolved. A modified or incomplete installed manifest is treated as
registry corruption rather than trusted package state.
