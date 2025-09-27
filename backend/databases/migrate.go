package databases

import (
	"embed"
	"fmt"
	"log"

	"github.com/golang-migrate/migrate/v4"
	"github.com/golang-migrate/migrate/v4/database/postgres"
	"github.com/golang-migrate/migrate/v4/source/iofs"
)

// Embed all SQL migration files
//
//go:embed migrations/*.sql
var migrationsFS embed.FS

func RunMigrations() {
	db := GetDB()
	if db == nil {
		log.Fatal("Database connection is nil — did you call InitDB()?")
	}

	driver, err := postgres.WithInstance(db, &postgres.Config{})
	if err != nil {
		log.Fatalf("Migration driver init failed: %v", err)
	}

	src, err := iofs.New(migrationsFS, "migrations")
	if err != nil {
		log.Fatalf("Migration source init failed: %v", err)
	}

	m, err := migrate.NewWithInstance("iofs", src, "postgres", driver)
	if err != nil {
		log.Fatalf("Migration setup failed: %v", err)
	}

	if err := m.Up(); err != nil {
		if err == migrate.ErrNoChange {
			fmt.Println("✅ Migrations: no change")
		} else {
			log.Fatalf("Migration failed: %v", err)
		}
	} else {
		fmt.Println("✅ Migrations applied")
	}
}
