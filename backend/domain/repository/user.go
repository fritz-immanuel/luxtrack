// backend/domain/repository/user.go
package repository

import (
	"context"
	"database/sql"

	"luxtrack-go/backend/domain/model"
)

type UserRepository interface {
	Insert(ctx context.Context, tx *sql.Tx, u *model.User) error
	Update(ctx context.Context, tx *sql.Tx, u *model.User) error
	Delete(ctx context.Context, tx *sql.Tx, id string) error

	// Reads do not use a tx by default
	FindByID(ctx context.Context, db *sql.DB, id string) (*model.User, error)
	FindByUsername(ctx context.Context, db *sql.DB, username string) (*model.User, error)
	List(ctx context.Context, db *sql.DB, limit, offset int) ([]model.User, error)
}
