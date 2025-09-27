// backend/internal/repository/product.go
package repository

import (
	"context"
	"database/sql"
	"luxtrack-go/backend/domain/model"
)

type productRepository struct{}

func NewProductRepository() *productRepository {
	return &productRepository{}
}

func (r *productRepository) Insert(ctx context.Context, tx *sql.Tx, p *model.Product) error {
	_, err := tx.ExecContext(ctx, `
		INSERT INTO products (product_id, name, brand_id, condition_id, status_id, seller_id, code)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`, p.ID, p.Name, p.BrandID, p.ConditionID, p.StatusID, p.SellerID, p.Code)
	return err
}

func (r *productRepository) SelectAll(ctx context.Context, db *sql.DB) ([]model.Product, error) {
	rows, err := db.QueryContext(ctx, `SELECT product_id, name, brand_id, condition_id, status_id, seller_id, code FROM products`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var products []model.Product
	for rows.Next() {
		var p model.Product
		if err := rows.Scan(&p.ID, &p.Name, &p.BrandID, &p.ConditionID, &p.StatusID, &p.SellerID, &p.Code); err != nil {
			return nil, err
		}
		products = append(products, p)
	}
	return products, nil
}

func (r *productRepository) Update(ctx context.Context, tx *sql.Tx, p *model.Product) error {
	_, err := tx.ExecContext(ctx, `
		UPDATE products
		SET name = $1, brand_id = $2, condition_id = $3, status_id = $4, seller_id = $5, code = $6
		WHERE product_id = $7
	`, p.Name, p.BrandID, p.ConditionID, p.StatusID, p.SellerID, p.Code, p.ID)
	return err
}

func (r *productRepository) Delete(ctx context.Context, tx *sql.Tx, id string) error {
	_, err := tx.ExecContext(ctx, `DELETE FROM products WHERE product_id = $1`, id)
	return err
}
