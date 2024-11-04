//go:build subfinder
// +build subfinder

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
)

var (
	name           = "subfinderScan"
	description    = "Performs subdomain enumeration on the target domain"
	author         = "Your Name"
	category       = "Web Application"
	installCommand = "go install github.com/subfinder/subfinder/v2/cmd/subfinder@latest" // Specify the install command for dependencies
	dependencies   = []string{"subfinder"}                                               // Specify required dependencies
	parameters     = []map[string]interface{}{
		{"name": "domain", "description": "Target domain", "required": true, "default": ""},
		{"name": "threads", "description": "Number of concurrent threads", "required": false, "default": "10"},
	}
)

func main() {
	metadata := flag.Bool("metadata", false, "Output metadata as JSON")
	var paramsJSON string
	flag.StringVar(&paramsJSON, "params", "", "JSON string containing module parameters")
	flag.Parse()

	if *metadata {
		// Output the metadata as JSON and exit
		meta := map[string]interface{}{
			"name":            name,
			"description":     description,
			"author":          author,
			"category":        category,
			"parameters":      parameters,
			"dependencies":    dependencies,
			"install_command": installCommand,
		}
		metaJSON, _ := json.Marshal(meta)
		fmt.Println(string(metaJSON))
		return
	}

	// Normal operation mode for executing the module logic
	var params struct {
		Domain  string `json:"domain"`
		Threads string `json:"threads"`
	}
	if err := json.Unmarshal([]byte(paramsJSON), &params); err != nil {
		fmt.Printf("{\"error\": \"Failed to parse parameters: %s\"}\n", err)
		os.Exit(1)
	}

	if params.Threads == "" {
		params.Threads = "10"
	}

	cmd := exec.Command("subfinder", "-d", params.Domain, "-t", params.Threads)
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("{\"error\": \"Failed to execute subfinder: %s\"}\n", err)
		os.Exit(1)
	}

	result := struct {
		Output string `json:"output"`
	}{
		Output: string(output),
	}
	resultJSON, _ := json.Marshal(result)
	fmt.Println(string(resultJSON))
}
