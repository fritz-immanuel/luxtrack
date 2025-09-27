// backend/internal/http/server.go
package http

import (
	"log"
	"time"

	"luxtrack-go/backend/config"
	"luxtrack-go/backend/databases"
	"luxtrack-go/backend/internal/http/middleware"
	"luxtrack-go/backend/internal/http/routes"
	repopkg "luxtrack-go/backend/internal/repository"
	serviceimpl "luxtrack-go/backend/internal/service"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"
)

func StartServer(cfg *config.Config) {
	app := fiber.New(fiber.Config{
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  30 * time.Second,
	})

	app.Use(recover.New())
	app.Use(logger.New())
	app.Use(cors.New(cors.Config{
		AllowOrigins: "*", // tighten in prod
		AllowHeaders: "Origin, Content-Type, Accept, Authorization",
	}))

	api := app.Group("/api")

	// DI
	db := databases.GetDB()

	// repositories
	productRepo := repopkg.NewProductRepository()
	userRepo := repopkg.NewUserRepository()

	// services
	productService := serviceimpl.NewProductService(db, productRepo)
	userService := serviceimpl.NewUserService(db, userRepo)

	// public routes
	routes.RegisterAuthRoutes(api, cfg, userService)

	// protected routes
	api.Use(middleware.RequireAuth(cfg))
	routes.RegisterProductRoutes(api, productService)

	log.Printf("🚀 Server started on %s\n", cfg.AppPort)
	log.Fatal(app.Listen(":" + cfg.AppPort))
}
