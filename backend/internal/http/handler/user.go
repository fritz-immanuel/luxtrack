// backend/internal/http/handler/user.go
package handler

import (
	"context"
	"strconv"

	"luxtrack-go/backend/domain/model"
	"luxtrack-go/backend/domain/service"
	"luxtrack-go/backend/internal/util/httphelper"

	"github.com/gofiber/fiber/v2"
)

type createUserReq struct {
	Username     string `json:"username"`
	Email        string `json:"email"`
	Role         string `json:"role"`
	ProfilePhoto string `json:"profile_photo"`
	Password     string `json:"password"`
}

func CreateUser(svc service.UserService) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var req createUserReq
		if err := c.BodyParser(&req); err != nil {
			return httphelper.JSONError(c, fiber.StatusBadRequest, "invalid payload")
		}

		u := &model.User{
			Username:     req.Username,
			Email:        req.Email,
			Role:         req.Role,
			ProfilePhoto: req.ProfilePhoto,
			CreatedBy:    c.Locals("email").(string),
			UpdatedBy:    c.Locals("email").(string),
		}

		if err := svc.Create(context.Background(), u, req.Password); err != nil {
			return httphelper.JSONError(c, fiber.StatusInternalServerError, err.Error())
		}
		return c.Status(fiber.StatusCreated).JSON(fiber.Map{"id": u.ID})
	}
}

func UpdateUser(svc service.UserService) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var u model.User
		if err := c.BodyParser(&u); err != nil {
			return httphelper.JSONError(c, fiber.StatusBadRequest, "invalid payload")
		}
		u.UpdatedBy = c.Locals("email").(string)

		if err := svc.Update(context.Background(), &u); err != nil {
			return httphelper.JSONError(c, fiber.StatusInternalServerError, err.Error())
		}
		return c.JSON(fiber.Map{"message": "updated"})
	}
}

func DeleteUser(svc service.UserService) fiber.Handler {
	return func(c *fiber.Ctx) error {
		id := c.Params("id")
		if id == "" {
			return httphelper.JSONError(c, fiber.StatusBadRequest, "missing id")
		}
		if err := svc.Delete(context.Background(), id); err != nil {
			return httphelper.JSONError(c, fiber.StatusInternalServerError, err.Error())
		}
		return c.JSON(fiber.Map{"message": "deleted"})
	}
}

func GetUserByID(svc service.UserService) fiber.Handler {
	return func(c *fiber.Ctx) error {
		id := c.Params("id")
		if id == "" {
			return httphelper.JSONError(c, fiber.StatusBadRequest, "missing id")
		}
		u, err := svc.FindByID(context.Background(), id)
		if err != nil {
			return httphelper.JSONError(c, fiber.StatusNotFound, "user not found")
		}
		u.PasswordHash = "" // ensure never leaked
		return c.JSON(u)
	}
}

func ListUsers(svc service.UserService) fiber.Handler {
	return func(c *fiber.Ctx) error {
		limit, _ := strconv.Atoi(c.Query("limit", "50"))
		offset, _ := strconv.Atoi(c.Query("offset", "0"))
		users, err := svc.List(context.Background(), limit, offset)
		if err != nil {
			return httphelper.JSONError(c, fiber.StatusInternalServerError, err.Error())
		}
		return c.JSON(users)
	}
}
