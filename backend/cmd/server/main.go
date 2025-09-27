// backend/cmd/server/main.go
package main

import (
	"fmt"
	"log"

	"luxtrack-go/backend/config"
	"luxtrack-go/backend/databases"
	"luxtrack-go/backend/internal/http"
)

func main() {
	fmt.Println("🚀 Server starting...")

	// Load config (from .env or system env)
	cfg, err := config.LoadConfig()
	if err != nil {
		log.Fatalf("❌ Failed to load config: %v", err)
	}

	// Initialize DB connection
	databases.InitDB()

	// Optional: run migrations from bindata
	databases.RunMigrations()

	// Start HTTP server (Fiber)
	http.StartServer(cfg)
	fmt.Println("Server running...")
}
