# Remote access over SSH and VPN

Run PQEnalyzer beside the simulation files on the server and open its web
interface in your desktop browser. The server reads and analyzes the original
files; the interface and chart data travel over an encrypted SSH connection.
No CSV conversion or manual transfer of the input files is required.

Only the server needs PQEnalyzer installed. Your desktop needs SSH and a browser.
Use your own username and server hostname in place of the examples below.

## From home over VPN

1. Connect your institution's VPN if it is required to reach the server.
2. Confirm that normal SSH access works from your desktop:

   ```bash
   ssh user@login.cluster
   ```

3. Start the app on that server, then open the tunnel from a second desktop
   terminal as shown below.

The same tunnel works from the institution's network and from home over VPN.
The VPN must provide a route to the SSH host and resolve its hostname, or your
institution must provide a reachable address or SSH alias. The SSH server must
allow TCP forwarding. Follow the cluster's policy for login and compute nodes.

## Start the app on the server

```bash
pqenalyzer web --no-open --port 8766 /path/to/simulation.en
```

See the [startup output](getting-started.md#server-startup). Leave this terminal
running; `Ctrl+C` stops the server.

Paths refer to files on the server. Keep each energy file's matching `.info`
file beside it. Supply multiple files in their dataset order when needed.

The app listens on `127.0.0.1:8766` on the server. Keep this default loopback
binding; remote access is provided by SSH.

## Open the tunnel on your desktop

```bash
ssh -N -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:8766:127.0.0.1:8766 user@login.cluster
```

Open <http://127.0.0.1:8766> in your desktop browser. The first address and port
are on your desktop; the second `127.0.0.1:8766` is reached from the SSH server.
The SSH destination must therefore be the machine running PQEnalyzer.

`-N` keeps SSH open for forwarding without starting a remote shell.
`ExitOnForwardFailure=yes` reports failure to establish the forwarding listener;
it does not check whether the web app is running.

## Compute node behind a login node

If your site permits SSH to an allocated compute node, start PQEnalyzer there
inside the allocation. Then use the login node as a jump host:

```bash
ssh -N -o ExitOnForwardFailure=yes -J user@login.cluster \
  -L 127.0.0.1:8766:127.0.0.1:8766 user@compute-node
```

The browser address remains <http://127.0.0.1:8766>. The final SSH destination is
the compute node hosting the app. Keep the allocation active for the session.

## Keep the session open

Keep both the app and SSH tunnel running. `Ctrl+C` in the tunnel terminal closes
the tunnel; stop the app separately when finished.

After a VPN or SSH disconnection, reconnect the VPN and rerun the tunnel
command. Restart the app too if its server session or allocation ended. The
browser can then reload the same local address.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| SSH times out or the hostname cannot be resolved | VPN connection, institutional DNS, hostname, and route to the SSH host. Use the same hostname or SSH alias as your normal login. |
| SSH login fails | Your SSH credentials and the site's access policy; establish normal SSH access first. |
| Forwarding is administratively prohibited | The site's SSH forwarding or compute-node access policy. Ask the cluster administrator which access path is supported. |
| Local address is already in use | Choose a different desktop port, as below. |
| The tunnel opens but the page does not | Check that the app is still running on the final SSH destination and that the remote port matches. From that server, try `curl --fail http://127.0.0.1:8766/api/status`. |

For a busy desktop port, change only the local port:

```bash
ssh -N -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:18766:127.0.0.1:8766 user@login.cluster
```

Then open <http://127.0.0.1:18766>. If port `8766` is busy on the server, choose
another `--port` for PQEnalyzer and use that value for the remote port in `-L`.

See the [OpenSSH manual](https://man.openbsd.org/ssh.1) for `-L`, `-N`, and `-J`.
