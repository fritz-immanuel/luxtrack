// backend/domain/service/user.go
package service

import (
	"context"

	"luxtrack-go/backend/domain/model"
)

type UserService interface {
	Create(ctx context.Context, u *model.User, plainPassword string) error
	Update(ctx context.Context, u *model.User) error
	Delete(ctx context.Context, id string) error

	FindByID(ctx context.Context, id string) (*model.User, error)
	List(ctx context.Context, limit, offset int) ([]model.User, error)

	// Authenticate returns the user on success
	Authenticate(ctx context.Context, username, password string) (*model.User, error)
}
