pipeline {
    agent any

    environment {
        ROOT_ENV                 = credentials('root-env')
        USER_SERVICE_ENV         = credentials('user-service-env')
        INCIDENT_SERVICE_ENV     = credentials('incident-report-service-env')
        NOTIFICATION_SERVICE_ENV = credentials('notification-service-env')
        TRAFFIC_SERVICE_ENV      = credentials('traffic-intelligence-service-env')
        API_GATEWAY_ENV          = credentials('api-gateway-env')
        RAG_SERVICE_ENV          = credentials('rag-service-env')
        FRONTEND_ENV             = credentials('frontend-env')
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Pulling latest code from GitHub...'
                checkout scm
            }
        }

        stage('Prepare Env Files') {
            steps {
                sh 'cp $ROOT_ENV .env'
                sh 'cp $USER_SERVICE_ENV services/user-service/.env'
                sh 'cp $INCIDENT_SERVICE_ENV services/incident-report-service/.env'
                sh 'cp $NOTIFICATION_SERVICE_ENV services/notification-service/.env'
                sh 'cp $TRAFFIC_SERVICE_ENV services/traffic-intelligence-service/.env'
                sh 'cp $API_GATEWAY_ENV services/api-gateway/.env'
                sh 'cp $RAG_SERVICE_ENV services/rag-service/.env'
                sh 'cp $FRONTEND_ENV frontend/.env'
            }
        }

        stage('Build') {
            steps {
                echo 'Building all Docker images...'
                sh 'docker compose build'
            }
        }

        stage('Test') {
            parallel {

                stage('Test: user-service') {
                    steps {
                        sh '''
                            CONTAINER=$(docker compose run --rm --no-deps -d user-service sleep 60)
                            docker exec $CONTAINER python -m pytest -v --junitxml=/tmp/results.xml || true
                            docker cp $CONTAINER:/tmp/results.xml ${WORKSPACE}/services/user-service/tests/results.xml || true
                            docker stop $CONTAINER || true
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/user-service/tests/results.xml'
                        }
                    }
                }

                stage('Test: incident-report-service') {
                    steps {
                        sh '''
                            CONTAINER=$(docker compose run --rm --no-deps -d incident-report-service sleep 60)
                            docker exec $CONTAINER python -m pytest -v --junitxml=/tmp/results.xml || true
                            docker cp $CONTAINER:/tmp/results.xml ${WORKSPACE}/services/incident-report-service/tests/results.xml || true
                            docker stop $CONTAINER || true
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/incident-report-service/tests/results.xml'
                        }
                    }
                }

                stage('Test: notification-service') {
                    steps {
                        sh '''
                            CONTAINER=$(docker compose run --rm --no-deps -d notification-service sleep 60)
                            docker exec $CONTAINER python -m pytest -v --junitxml=/tmp/results.xml || true
                            docker cp $CONTAINER:/tmp/results.xml ${WORKSPACE}/services/notification-service/tests/results.xml || true
                            docker stop $CONTAINER || true
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/notification-service/tests/results.xml'
                        }
                    }
                }

                stage('Test: traffic-intelligence-service') {
                    steps {
                        sh '''
                            CONTAINER=$(docker compose run --rm --no-deps -d traffic-intelligence-service sleep 60)
                            docker exec $CONTAINER python -m pytest -v --junitxml=/tmp/results.xml || true
                            docker cp $CONTAINER:/tmp/results.xml ${WORKSPACE}/services/traffic-intelligence-service/tests/results.xml || true
                            docker stop $CONTAINER || true
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/traffic-intelligence-service/tests/results.xml'
                        }
                    }
                }

                stage('Test: api-gateway') {
                    steps {
                        sh '''
                            CONTAINER=$(docker compose run --rm --no-deps -d api-gateway sleep 60)
                            docker exec $CONTAINER python -m pytest -v --junitxml=/tmp/results.xml || true
                            docker cp $CONTAINER:/tmp/results.xml ${WORKSPACE}/services/api-gateway/tests/results.xml || true
                            docker stop $CONTAINER || true
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/api-gateway/tests/results.xml'
                        }
                    }
                }

                stage('Test: rag-service') {
                    steps {
                        sh '''
                            CONTAINER=$(docker compose run --rm --no-deps -d rag-service sleep 60)
                            docker exec $CONTAINER python -m pytest -v --junitxml=/tmp/results.xml || true
                            docker cp $CONTAINER:/tmp/results.xml ${WORKSPACE}/services/rag-service/tests/results.xml || true
                            docker stop $CONTAINER || true
                        '''
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'services/rag-service/tests/results.xml'
                        }
                    }
                }

            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo 'Deploying UrbanFlow to production...'
                sh 'docker compose down'
                sh 'docker compose up -d'
            }
        }

    }

    post {
        always {
            echo "Pipeline finished on branch: ${env.BRANCH_NAME}"
            sh 'docker compose down || true'
        }
        success {
            echo 'UrbanFlow deployed successfully'
        }
        failure {
            echo 'Pipeline failed - check test results'
        }
    }

}