# Call Lifecycle

!!! note "Draft"
    This page is being written. It will cover:

    - Which Kedi statement calls which entry point, with which keyword arguments
    - Order of scopes Kedi enters: profile override, tool scope, conversation scope, required-tool scope, artifact scope
    - Sync and async entry points and `run_sync`
    - Kedi-side validation and conversation commit after the call
