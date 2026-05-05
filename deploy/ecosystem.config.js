// PM2 ecosystem para o backend FastAPI.
// Frontend é estático (build em frontend/dist), servido pelo Nginx.

module.exports = {
  apps: [
    {
      name: "assistente-social-media-backend",
      cwd: "/opt/assistente-social-media-backend",
      script: ".venv/bin/uvicorn",
      args: "app.main:app --host 127.0.0.1 --port 3002 --workers 2",
      interpreter: "none",
      watch: false,
      autorestart: true,
      max_memory_restart: "512M",
      env: {
        APP_ENV: "production",
        APP_PORT: "3002",
        AUTH_BYPASS: "false",
      },
      out_file: "/var/log/orbitaia/social-media-backend.out.log",
      error_file: "/var/log/orbitaia/social-media-backend.err.log",
      time: true,
    },
  ],
};
