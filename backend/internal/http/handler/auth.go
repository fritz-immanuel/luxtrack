// backend/internal/http/handler/auth_handler.go
package handler

import (
	"context"
	"strings"

	"luxtrack-go/backend/config"
	"luxtrack-go/backend/domain/service"
	"luxtrack-go/backend/internal/util/httphelper"
	"luxtrack-go/backend/internal/util/jwtutil"

	"github.com/gofiber/fiber/v2"
)

type loginReq struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

func LoginWithUserService(cfg *config.Config, us service.UserService) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var req loginReq
		if err := c.BodyParser(&req); err != nil {
			return httphelper.JSONError(c, fiber.StatusBadRequest, "invalid payload")
		}
		req.Username = strings.TrimSpace(req.Username)

		u, err := us.Authenticate(context.Background(), req.Username, req.Password)
		if err != nil {
			return httphelper.JSONError(c, fiber.StatusUnauthorized, "invalid credentials")
		}

		token, err := jwtutil.GenerateJWT(cfg, u.Username)
		if err != nil {
			return httphelper.JSONError(c, fiber.StatusInternalServerError, "could not generate token")
		}

		return c.JSON(fiber.Map{
			"token": token,
			"user": fiber.Map{
				"id":       u.ID,
				"username": u.Username,
				"role":     u.Role,
				"email":    u.Email,
			},
		})
	}
}
