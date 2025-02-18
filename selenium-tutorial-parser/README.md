# Selenium Tutorial Parser

1. Add chrome path to environment variables. Then refresh current terminal environment variables or open new terminal.

    ```powershell
    [System.Environment]::SetEnvironmentVariable('path', "C:\Program Files\Google\Chrome\Application;" + [System.Environment]::GetEnvironmentVariable('path', "User"),"User")
    ```

2. Launch browser with remote debugging.

    ```powershell
    chrome --remote-debugging-port=9222
    ```

## References

1. [Can Selenium interact with an existing browser session?](https://stackoverflow.com/a/70088095)
