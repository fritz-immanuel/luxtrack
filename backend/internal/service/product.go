// backend/internal/service/product.go
package serviceimpl

import (
	"context"
	"database/sql"

	"luxtrack-go/backend/domain/model"
	"luxtrack-go/backend/domain/repository"
	"luxtrack-go/backend/domain/service"
)

type productService struct {
	db          *sql.DB
	productRepo repository.ProductRepository
}

func NewProductService(db *sql.DB, productRepo repository.ProductRepository) service.ProductService {
	return &productService{
		db:          db,
		productRepo: productRepo,
	}
}

func (s *productService) Create(ctx context.Context, p *model.Product) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	if err := s.productRepo.Insert(ctx, tx, p); err != nil {
		return err
	}

	return tx.Commit()
}

func (s *productService) FindAll(ctx context.Context) ([]model.Product, error) {
	return s.productRepo.SelectAll(ctx, s.db)
}

func (s *productService) Update(ctx context.Context, p *model.Product) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	if err := s.productRepo.Update(ctx, tx, p); err != nil {
		return err
	}

	return tx.Commit()
}

func (s *productService) Delete(ctx context.Context, id string) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	if err := s.productRepo.Delete(ctx, tx, id); err != nil {
		return err
	}

	return tx.Commit()
}
