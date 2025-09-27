// backend/internal/service/user.go
package serviceimpl

import (
	"context"
	"database/sql"
	"errors"

	"luxtrack-go/backend/domain/model"
	"luxtrack-go/backend/domain/repository"
	"luxtrack-go/backend/domain/service"
	"luxtrack-go/backend/internal/util/password"

	"github.com/google/uuid"
)

type userService struct {
	db   *sql.DB
	repo repository.UserRepository
}

func NewUserService(db *sql.DB, repo repository.UserRepository) service.UserService {
	return &userService{db: db, repo: repo}
}

func (s *userService) Create(ctx context.Context, u *model.User, plainPassword string) error {
	if u.ID == "" {
		u.ID = uuid.NewString()
	}
	hash, err := password.Hash(plainPassword)
	if err != nil {
		return err
	}
	u.PasswordHash = hash

	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	if err := s.repo.Insert(ctx, tx, u); err != nil {
		return err
	}
	return tx.Commit()
}

func (s *userService) Update(ctx context.Context, u *model.User) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	if err := s.repo.Update(ctx, tx, u); err != nil {
		return err
	}
	return tx.Commit()
}

func (s *userService) Delete(ctx context.Context, id string) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	if err := s.repo.Delete(ctx, tx, id); err != nil {
		return err
	}
	return tx.Commit()
}

func (s *userService) FindByID(ctx context.Context, id string) (*model.User, error) {
	return s.repo.FindByID(ctx, s.db, id)
}

func (s *userService) List(ctx context.Context, limit, offset int) ([]model.User, error) {
	return s.repo.List(ctx, s.db, limit, offset)
}

func (s *userService) Authenticate(ctx context.Context, username, plain string) (*model.User, error) {
	u, err := s.repo.FindByUsername(ctx, s.db, username)
	if err != nil {
		return nil, err
	}
	if err := password.Verify(plain, u.PasswordHash); err != nil {
		return nil, errors.New("invalid credentials")
	}
	return u, nil
}
