// backend/domain/repository/product_repository.go
package repository

import (
	"context"
	"database/sql"
	"luxtrack-go/backend/domain/model"
)

type ProductRepository interface {
	Insert(ctx context.Context, tx *sql.Tx, p *model.Product) error
	SelectAll(ctx context.Context, db *sql.DB) ([]model.Product, error)
	Update(ctx context.Context, tx *sql.Tx, p *model.Product) error
	Delete(ctx context.Context, tx *sql.Tx, id string) error
}
