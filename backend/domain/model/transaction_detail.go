// backend/domain/model/transaction_detail.go
package model

import "time"

type TransactionDetail struct {
	ID            string    `json:"id"`
	TransactionID string    `json:"transaction_id"`
	ProductID     string    `json:"product_id"`
	Quantity      int       `json:"quantity"`
	Price         float64   `json:"price"`
	CreatedBy     string    `json:"created_by"`
	CreatedAt     time.Time `json:"created_at"`
	UpdatedBy     string    `json:"updated_by"`
	UpdatedAt     time.Time `json:"updated_at"`
}
