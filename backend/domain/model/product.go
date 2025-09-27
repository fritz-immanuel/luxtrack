// backend/domain/model/product.go
package model

import "time"

type Product struct {
	ID            string    `json:"id"`
	Code          string    `json:"code"`
	Name          string    `json:"name"`
	Description   string    `json:"description"`
	ConditionID   int       `json:"condition_id"`
	StatusID      int       `json:"status_id"`
	CategoryID    int       `json:"category_id"`
	BrandID       int       `json:"brand_id"`
	SellerID      string    `json:"seller_id"`
	Price         float64   `json:"price"`
	PurchasePrice float64   `json:"purchase_price"`
	StockQty      int       `json:"stock_qty"`
	CreatedBy     string    `json:"created_by"`
	CreatedAt     time.Time `json:"created_at"`
	UpdatedBy     string    `json:"updated_by"`
	UpdatedAt     time.Time `json:"updated_at"`
}
