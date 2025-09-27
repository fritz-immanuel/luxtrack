// backend/internal/http/handler/product.go
package handler

import (
	"context"

	"luxtrack-go/backend/domain/model"
	"luxtrack-go/backend/domain/service"
	"luxtrack-go/backend/internal/util/httphelper"

	"github.com/gofiber/fiber/v2"
)

// CreateProduct handles POST /api/products
// - parses JSON into model.Product
// - calls service with transaction inside
func CreateProduct(svc service.ProductService) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var p model.Product
		if err := c.BodyParser(&p); err != nil {
			return httphelper.JSONError(c, fiber.StatusBadRequest, "invalid payload")
		}
		if err := svc.Create(context.Background(), &p); err != nil {
			return httphelper.JSONError(c, fiber.StatusInternalServerError, err.Error())
		}
		return c.Status(fiber.StatusCreated).JSON(fiber.Map{"message": "Product created"})
	}
}

// GetAllProducts handles GET /api/products
func GetAllProducts(svc service.ProductService) fiber.Handler {
	return func(c *fiber.Ctx) error {
		list, err := svc.FindAll(context.Background())
		if err != nil {
			return httphelper.JSONError(c, fiber.StatusInternalServerError, err.Error())
		}
		return c.JSON(list)
	}
}
