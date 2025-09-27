// backend/internal/util/httphelper/httphelper.go
package httphelper

import "github.com/gofiber/fiber/v2"

func JSONError(c *fiber.Ctx, code int, message string) error {
	return c.Status(code).JSON(fiber.Map{"error": message})
}

func JSONOK(c *fiber.Ctx, data any) error {
  return c.Status(fiber.StatusOK).JSON(data)
}