# Weasley Clock Location Server

This directory contains a node.js server that listens on port 3000. The .htaccess file in the root directory of the shared dreamhost hosting routes incoming https requests to localhost:3000 and node interprets them:
```
RewriteEngine On
RewriteRule ^(.*)$ http://localhost:3000/$1 [P]
```
The server uses the Express framework and a MySQL database. It provides endpoints for updating and fetching location data and includes a scheduled task to clear old entries from the database every 10 minutes.

### Setup

The authorization that protects the `/get_locations` endpoint reads a SECRET_TOKEN from a .env file using the dotenv npm package, so make sure to set up your own.

### Usage

1. Start the server using PM2.

```bash
pm2 start server.js
```

2. List all running processes managed by PM2.

```bash
pm2 list
```

3. Stop the server by its app name listed in the list output above.

```bash
pm2 stop <app-name>
```

4. See logs

```bash
pm2 logs
```

5. Endpoints:

- **POST `/update_location`**: Insert location data.

  Example using `curl`:

  ```bash
  curl -X POST \
       -H "Content-Type: application/json" \
       -d '{"name":"kappi","coordinates":"POINT(-33.93977815657354 18.416488657913117)"}' \
       https://api.thinkkappi.com/update_location
  ```

- **GET `/get_locations`**: Fetch all location data.

- **Scheduled Task**: The server runs a task to clear old location entries from the database every 10 minutes. Entries older than one day will be deleted.

