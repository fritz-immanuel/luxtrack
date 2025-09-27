package databases

import (
	"bytes"
	"io"
	"io/fs"
	"os"
	"sync"

	rice "github.com/GeertJohan/go.rice"
	"github.com/golang-migrate/migrate/v4/source"
)

type RiceBoxSource struct {
	lock       sync.Mutex
	box        *rice.Box
	migrations *source.Migrations
}

func (s *RiceBoxSource) loadMigrations() (*source.Migrations, error) {
	migrations := source.NewMigrations()
	err := s.box.Walk("", func(path string, info fs.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if info.IsDir() {
			return nil
		}
		m, err := source.Parse(path)
		if err != nil {
			return err
		}
		migrations.Append(m)
		return nil
	})
	return migrations, err
}

func (s *RiceBoxSource) PopulateMigrations(box *rice.Box) error {
	s.lock.Lock()
	defer s.lock.Unlock()
	s.box = box
	m, err := s.loadMigrations()
	if err != nil {
		return err
	}
	s.migrations = m
	return nil
}

func (s *RiceBoxSource) Open(_ string) (source.Driver, error) { return s, nil }
func (s *RiceBoxSource) Close() error                         { return nil }

func (s *RiceBoxSource) First() (uint, error) {
	v, ok := s.migrations.First()
	if !ok {
		return 0, os.ErrNotExist
	}
	return v, nil
}

func (s *RiceBoxSource) Prev(version uint) (uint, error) {
	v, ok := s.migrations.Prev(version)
	if !ok {
		return 0, os.ErrNotExist
	}
	return v, nil
}

func (s *RiceBoxSource) Next(version uint) (uint, error) {
	v, ok := s.migrations.Next(version)
	if !ok {
		return 0, os.ErrNotExist
	}
	return v, nil
}

func (s *RiceBoxSource) ReadUp(version uint) (io.ReadCloser, string, error) {
	m, ok := s.migrations.Up(version)
	if !ok {
		return nil, "", os.ErrNotExist
	}
	b, err := s.box.Bytes(m.Raw)
	if err != nil {
		return nil, "", err
	}
	return io.NopCloser(bytes.NewReader(b)), m.Identifier, nil
}

func (s *RiceBoxSource) ReadDown(version uint) (io.ReadCloser, string, error) {
	m, ok := s.migrations.Down(version)
	if !ok {
		return nil, "", os.ErrNotExist
	}
	b, err := s.box.Bytes(m.Raw)
	if err != nil {
		return nil, "", err
	}
	return io.NopCloser(bytes.NewReader(b)), m.Identifier, nil
}
