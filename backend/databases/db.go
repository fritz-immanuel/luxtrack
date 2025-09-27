package databases

import (
	"database/sql"
	"fmt"
	"log"

	"luxtrack-go/backend/config"

	_ "github.com/lib/pq" // PostgreSQL driver
)

var db *sql.DB

func InitDB() {
	cfg := config.Get()

	dsn := fmt.Sprintf(
		"postgres://%s:%s@%s:%d/%s?sslmode=disable",
		cfg.DBUser,
		cfg.DBPass,
		cfg.DBHost,
		cfg.DBPort,
		cfg.DBName,
	)

	var err error
	db, err = sql.Open("postgres", dsn)
	if err != nil {
		log.Fatalf("Failed to open DB: %v", err)
	}

	if err = db.Ping(); err != nil {
		log.Fatalf("Failed to connect to DB: %v", err)
	}

	fmt.Println("✅ Database connected")
}

func GetDB() *sql.DB {
	return db
}
