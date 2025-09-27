// backend/domain/service/product_service.go
package service

import (
	"context"
	"luxtrack-go/backend/domain/model"
)

type ProductService interface {
	Create(ctx context.Context, p *model.Product) error
	FindAll(ctx context.Context) ([]model.Product, error)
	Update(ctx context.Context, p *model.Product) error
	Delete(ctx context.Context, id string) error
}
