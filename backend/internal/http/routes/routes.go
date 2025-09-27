// backend/internal/http/routes/routes.go
package routes

import (
	"luxtrack-go/backend/config"
	"luxtrack-go/backend/domain/service"
	"luxtrack-go/backend/internal/http/handler"

	"github.com/gofiber/fiber/v2"
)

// Auth now expects the UserService for real authentication.
func RegisterAuthRoutes(router fiber.Router, cfg *config.Config, us service.UserService) {
	auth := router.Group("/auth")
	auth.Post("/login", handler.LoginWithUserService(cfg, us))
}

func RegisterProductRoutes(router fiber.Router, ps service.ProductService) {
	p := router.Group("/products")
	p.Post("/", handler.CreateProduct(ps))
	p.Get("/", handler.GetAllProducts(ps))
}
