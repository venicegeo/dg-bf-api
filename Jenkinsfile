@Library('pipelib@master') _

node {

    stage('Setup') {
        git([
            url: 'https://github.com/venicegeo/dg-bf-api.git',
            branch: 'master'
        ])
    }

    stage('Test') {
        sh 'echo y | ./scripts/test.sh'
    }

    stage('Archive') {
        sh 'echo y | ./scripts/package.sh'
    }

    stage('Create CloudFoundry manifest') {
        def props = readProperties(file: 'jenkins.properties')

        withEnv([
            "MANIFEST_OUTFILE=${props.get('cfManifest')}",
            "CATALOG_HOST=bf-ia-broker.${props.get('cfDomain')}",
            "PIAZZA_HOST=piazza.${props.get('cfDomain')}"
        ]) {
            withCredentials([[
                $class: 'UsernamePasswordBinding',
                credentialsId: 'beachfront-piazza-npe',
                variable: 'PIAZZA_AUTH'
            ]]) {
                sh 'echo y | ./scripts/create-cf-manifest.sh'
            }
        }
    }

    stage('Deploy') {
        try {
		cfPush()
        	cfBgDeploy()
	} finally {
		stage('Cleanup')
	}
    }

    stage('Cleanup') {
        deleteDir()
    }
}
