// backend/internal/repository/user.go
package repository

import (
	"context"
	"database/sql"

	"luxtrack-go/backend/domain/model"
)

type userRepository struct{}

func NewUserRepository() *userRepository { return &userRepository{} }

func (r *userRepository) Insert(ctx context.Context, tx *sql.Tx, u *model.User) error {
	_, err := tx.ExecContext(ctx, `
    INSERT INTO users (id, username, password_hash, role, email, profile_photo, last_login, created_by, created_at, updated_by, updated_at)
    VALUES ($1,$2,$3,$4,$5,$6,$7,$8, NOW(), $9, NOW())
  `, u.ID, u.Username, u.PasswordHash, u.Role, u.Email, u.ProfilePhoto, u.LastLogin, u.CreatedBy, u.UpdatedBy)
	return err
}

func (r *userRepository) Update(ctx context.Context, tx *sql.Tx, u *model.User) error {
	_, err := tx.ExecContext(ctx, `
    UPDATE users
       SET username=$1, role=$2, email=$3, profile_photo=$4, updated_by=$5, updated_at=NOW()
     WHERE id=$6
  `, u.Username, u.Role, u.Email, u.ProfilePhoto, u.UpdatedBy, u.ID)
	return err
}

func (r *userRepository) Delete(ctx context.Context, tx *sql.Tx, id string) error {
	_, err := tx.ExecContext(ctx, `DELETE FROM users WHERE id=$1`, id)
	return err
}

func (r *userRepository) FindByID(ctx context.Context, db *sql.DB, id string) (*model.User, error) {
	row := db.QueryRowContext(ctx, `
    SELECT id, username, password_hash, role, email, profile_photo, last_login, created_by, created_at, updated_by, updated_at
      FROM users WHERE id=$1
  `, id)

	var u model.User
	if err := row.Scan(&u.ID, &u.Username, &u.PasswordHash, &u.Role, &u.Email, &u.ProfilePhoto, &u.LastLogin, &u.CreatedBy, &u.CreatedAt, &u.UpdatedBy, &u.UpdatedAt); err != nil {
		return nil, err
	}
	return &u, nil
}

func (r *userRepository) FindByUsername(ctx context.Context, db *sql.DB, username string) (*model.User, error) {
	row := db.QueryRowContext(ctx, `
    SELECT id, username, password_hash, role, email, profile_photo, last_login, created_by, created_at, updated_by, updated_at
      FROM users WHERE username=$1
  `, username)

	var u model.User
	if err := row.Scan(&u.ID, &u.Username, &u.PasswordHash, &u.Role, &u.Email, &u.ProfilePhoto, &u.LastLogin, &u.CreatedBy, &u.CreatedAt, &u.UpdatedBy, &u.UpdatedAt); err != nil {
		return nil, err
	}
	return &u, nil
}

func (r *userRepository) List(ctx context.Context, db *sql.DB, limit, offset int) ([]model.User, error) {
	if limit <= 0 {
		limit = 50
	}
	rows, err := db.QueryContext(ctx, `
    SELECT id, username, role, email, profile_photo, last_login, created_by, created_at, updated_by, updated_at
      FROM users
     ORDER BY created_at DESC
     LIMIT $1 OFFSET $2
  `, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []model.User
	for rows.Next() {
		var u model.User
		if err := rows.Scan(&u.ID, &u.Username, &u.Role, &u.Email, &u.ProfilePhoto, &u.LastLogin, &u.CreatedBy, &u.CreatedAt, &u.UpdatedBy, &u.UpdatedAt); err != nil {
			return nil, err
		}
		out = append(out, u)
	}
	return out, nil
}
