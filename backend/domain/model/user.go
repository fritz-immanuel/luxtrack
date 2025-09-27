// backend/domain/model/user.go
package model

import "time"

// User matches the DB schema from migrations.
type User struct {
	ID           string     `json:"id"`
	Username     string     `json:"username"`
	Email        string     `json:"email,omitempty"`
	Role         string     `json:"role"`
	ProfilePhoto string     `json:"profile_photo,omitempty"`
	LastLogin    *time.Time `json:"last_login,omitempty"`

	// Internal fields (not exposed in JSON)
	PasswordHash string    `json:"-"` // never return this
	CreatedBy    string    `json:"created_by,omitempty"`
	CreatedAt    time.Time `json:"created_at"`
	UpdatedBy    string    `json:"updated_by,omitempty"`
	UpdatedAt    time.Time `json:"updated_at"`
}
