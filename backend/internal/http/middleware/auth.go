// backend/internal/http/middleware/auth.go
package middleware

import (
	"luxtrack-go/backend/config"
	"luxtrack-go/backend/internal/util/httphelper"
	"luxtrack-go/backend/internal/util/jwtutil"

	"github.com/gofiber/fiber/v2"
)

func RequireAuth(cfg *config.Config) fiber.Handler {
	return func(c *fiber.Ctx) error {
		authHeader := c.Get("Authorization")
		tokenStr := jwtutil.ExtractBearerToken(authHeader)
		if tokenStr == "" {
			return httphelper.JSONError(c, fiber.StatusUnauthorized, "Missing or malformed token")
		}

		claims, err := jwtutil.ValidateJWT(cfg, tokenStr)
		if err != nil {
			return httphelper.JSONError(c, fiber.StatusUnauthorized, err.Error())
		}

		c.Locals("email", claims["email"])
		return c.Next()
	}
}
