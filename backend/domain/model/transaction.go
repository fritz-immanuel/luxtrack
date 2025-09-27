// backend/domain/model/transaction.go
package model

import "time"

type Transaction struct {
	ID               string     `json:"id"`
	CustomerID       string     `json:"customer_id"`
	PaymentMethodID  int        `json:"payment_method_id"`
	ShippingMethodID int        `json:"shipping_method_id"`
	ShippingFee      float64    `json:"shipping_fee"`
	ArrivalAt        *time.Time `json:"arrival_at,omitempty"`
	DeliveredAt      *time.Time `json:"delivered_at,omitempty"`
	Note             string     `json:"note"`
	CreatedBy        string     `json:"created_by"`
	CreatedAt        time.Time  `json:"created_at"`
	UpdatedBy        string     `json:"updated_by"`
	UpdatedAt        time.Time  `json:"updated_at"`
}
