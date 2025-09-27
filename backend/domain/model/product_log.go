// backend/domain/model/product_log.go
package model

import "time"

type ProductLog struct {
	ID        string    `json:"id"`
	ProductID string    `json:"product_id"`
	Action    string    `json:"action"`
	Note      string    `json:"note"`
	CreatedBy string    `json:"created_by"`
	CreatedAt time.Time `json:"created_at"`
}
