package semreg_thermal_map_contract

import (
	"encoding/json"
	"os"
	"testing"

	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/graph"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/projection"
)

// This validates the synthetic acceptance binding, not source qualification.
func TestDHWSetpointRowAgainstTheElementInventory(t *testing.T) {
	data, err := os.ReadFile("../../architecture/fixtures/dhw-setpoint-semreg-cutover-v1.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		Rows []struct {
			NativeKey string `json:"native_key"`
			Target    target `json:"target"`
			Subject   struct {
				Status string `json:"status"`
			} `json:"subject"`
		} `json:"rows"`
		ProjectionCases []struct {
			Case         string                             `json:"case"`
			Requested    []projection.RequestedItem         `json:"requested"`
			Dispositions []projection.ProjectionDisposition `json:"dispositions"`
		} `json:"projection_cases"`
	}
	if err := json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	if len(fixture.Rows) != 1 {
		t.Fatal("expected one native hot-water row")
	}
	row := fixture.Rows[0]
	catalog := loadInventory(t)
	if err := checkTarget(catalog, row.Target); err != nil {
		t.Fatalf("%s: %v", row.NativeKey, err)
	}
	entry, _ := catalog.PackEntry(row.Target.Definition)
	if row.Subject.Status != string(graph.SubjectUnresolved) || entry.Fact.Subject.Status != graph.SubjectUnresolved {
		t.Fatalf("%s: the service identity gap is an unresolved subject, got %q", row.NativeKey, row.Subject.Status)
	}
	if len(fixture.ProjectionCases) != 2 {
		t.Fatal("expected the two-service and partial-absence cases")
	}
	for _, c := range fixture.ProjectionCases {
		if len(c.Requested) != 1 || len(c.Dispositions) != 1 {
			t.Fatalf("%s: one disposition per requested item", c.Case)
		}
		disposition := c.Dispositions[0]
		if err := disposition.Validate(); err != nil {
			t.Fatalf("%s: disposition is not a valid projection disposition: %v", c.Case, err)
		}
		if disposition.Kind != c.Requested[0].Kind || disposition.ItemID != c.Requested[0].ItemID || disposition.ItemID != row.Target.Definition.ID {
			t.Fatalf("%s: disposition names another item", c.Case)
		}
		if disposition.Outcome != projection.ProjectionWithheld || len(disposition.SourceKeys) != 0 {
			t.Fatalf("%s: an unresolved subject is withheld with no source key", c.Case)
		}
		if len(disposition.Loss) != 0 {
			t.Fatalf("%s: the service identity gap is not a projection loss", c.Case)
		}
		if disposition.Reason == nil || *disposition.Reason != entry.Reason {
			t.Fatalf("%s: withheld reason differs from the inventory reason %q", c.Case, entry.Reason)
		}
	}
}
